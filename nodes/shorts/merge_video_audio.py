from config.settings import settings
from states.shorts_state import ShortsState
import os
from datetime import datetime
import uuid
from urllib.parse import quote
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def merge_video_with_audio(state: ShortsState) -> ShortsState:
    """영상 + 오디오 + 마지막 Fadeout (2.5초) """
    if not state.final_video_path or not state.music_files:
        print("영상 또는 오디오 파일 없음")
        
        return state

    # 음악 fadeout 설정
    music_fadeout_seconds = 2.5
    
    os.makedirs(state.final_video_audio_dir, exist_ok = True)

    try:
        # 비디오 & 오디오 로드
        video = VideoFileClip(state.final_video_path)
        audio = AudioFileClip(state.music_files[1])

        video_duration = video.duration
        audio_duration = audio.duration

        print(f"영상 길이: {video_duration:.2f}초")
        print(f"오디오 길이: {audio_duration:.2f}초")

        
        # 오디오를 영상 길이에 맞춤
        if audio_duration > video_duration:
            audio = audio.subclip(0, video_duration)

        
        # 페이드아웃 시작 시점 지정
        fadeout_start_time = max(0, video_duration - music_fadeout_seconds)

        print(f"페이드아웃 시작: {fadeout_start_time:.2f}초")
        print(f"페이드아웃 종료: {video_duration:.2f}초")

        output_path = os.path.join(state.final_video_audio_dir, state.final_video_audio_filename)

        # 오디오를 두 부분으로 나누기
        if fadeout_start_time > 0:
            # 페이드아웃 전 부분
            audio_before_fade = audio.subclip(0, fadeout_start_time)

            # 페이드아웃 부분
            audio_fade_part = audio.subclip(fadeout_start_time, video_duration)
            audio_fade_part = audio_fade_part.audio_fadeout(music_fadeout_seconds)

            # 두 부분 합치기
            final_audio = concatenate_audioclips([audio_before_fade, audio_fade_part])

        else:
            # 전체 오디오에 페이드아웃 적용
            final_audio = audio.audio_fadeout(music_fadeout_seconds)

        
        # 영상에 오디오 적용
        final_video = video.set_audio(final_audio)

        # 출력
        print("영상 + 오디오 머지 중...")
        final_video.write_videofile(
            output_path,
            codec = 'libx264',
            audio_codec = 'aac',
            fps = 24,
            bitrate = '12000k',
            temp_audiofile = 'temp-audio.m4a',
            remove_temp = True
        )

        # 메모리 정리
        video.close()
        audio.close()

        final_audio.close()
        final_video.close()

        print("영상 + 오디오 머지 완료\n")
        print(f"최종 영상 생성 완료: {output_path}")
        
        s3_key = upload_video_s3(output_path)

        state.final_video_audio_path = output_path
        state.final_video_audio_filename = os.path.basename(output_path)

        state.key = s3_key
        

        return state

    except Exception as e:
        raise Exception(f"최종 영상(오디오 포함) 생성 실패: {e}")


def upload_video_s3(video_path: str) -> str:
    """ 영상 파일을 S3에 업로드하고 key를 반환 """
    
    try:
        # S3 boto 설정 (최종 비디오 파일 저장)
        s3_client = boto3.client(
            's3',
            aws_access_key_id = settings.aws_access_key_id,
            aws_secret_access_key = settings.aws_secret_access_key,
            region_name = settings.aws_default_region
        )
        
        bucket_name = 'aivle-temp'

        original_filename = os.path.basename(video_path)
        
        # key 생성 (uuid-비디오 파일명)
        key = f"{uuid.uuid4()}-{quote(original_filename)}"
        
        print(f"S3 업로드: s3://{bucket_name}/{key}")
        

        s3_client.upload_file(
            Filename = video_path,
            Bucket = bucket_name,
            Key = key
        )

        print(f"S3 업로드 완료: {key}")
        
        return key
    
    
    # Exceptions
    except NoCredentialsError:
        error_msg = "AWS credentials가 설정되지 않음"
        print(f"S3 업로드 실패: {error_msg}")
        raise Exception(error_msg)
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"S3 업로드 실패 (ClientError): {error_code} - {e}")
        raise Exception(f"S3 업로드 실패: {e}")
    
    except Exception as e:
        print(f"S3 업로드 실패: {e}")
        raise Exception(f"S3 업로드 실패: {e}")
