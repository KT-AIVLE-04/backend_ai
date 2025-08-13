from typing import List
import requests
import base64
from io import BytesIO
from PIL import Image

def download_and_encode_image(url):
    """이미지 URL을 다운로드하고 base64로 인코딩"""
    try:
        response = requests.get(url)
        response.raise_for_status()

        # 이미지를 PIL로 열어서 처리
        image = Image.open(BytesIO(response.content))

        # RGBA나 다른 모드를 RGB로 변환
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')

        # 이미지 크기 최적화
        max_size = (1024, 1024)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # base64로 인코딩
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return image_base64
    except Exception as e:
        print(f"이미지 처리 실패 ({url}): {e}")
        return None

def combine_images(image_url: List[str]):
    # URL에서 이미지 불러오기
    images = []
    for url in image_url:
        try:
            response = requests.get(url)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            images.append(img)
        except Exception as e:
            print(f"이미지 로드 실패 ({url}): {e}")
            continue
    
    if not images:
        raise ValueError("유효한 이미지가 없습니다")

    # 이미지 크기 맞추기 (가장 작은 높이에 맞춰 리사이즈)
    min_height = min(img.height for img in images)
    resized_images = [img.resize((int(img.width * min_height / img.height), min_height)) for img in images]

    # 가로로 이어붙이기
    total_width = sum(img.width for img in resized_images)
    combined_img = Image.new("RGB", (total_width, min_height))

    x_offset = 0
    for img in resized_images:
        combined_img.paste(img, (x_offset, 0))
        x_offset += img.width

    # 메모리에서 바로 Base64 URL 변환
    buffer = BytesIO()
    combined_img.save(buffer, format="JPEG")  # JPEG 포맷으로 저장
    base64_string = base64.b64encode(buffer.getvalue()).decode("utf-8")
    base64_url = f"data:image/jpeg;base64,{base64_string}"

    return base64_url