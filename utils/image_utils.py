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