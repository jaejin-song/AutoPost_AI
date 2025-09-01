# 공통 함수
from typing import List
from datetime import datetime
import os

from modules.ai.content_writer import Post

def clean_text(text: str) -> str:
    return text.strip()

def save_posts_to_file(posts: List[Post], filename: str = None) -> str:
    """Post 리스트를 텍스트 파일로 저장 (테스트용)"""
    
    if not posts:
        print("저장할 포스트가 없습니다.")
        return ""
    
    # 파일명 생성 (제공되지 않으면 자동 생성)
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"posts_preview_{timestamp}.txt"
    
    # data 폴더에 저장
    data_dir = "data/posts"
    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"포스트 미리보기 ({len(posts)}개)\n")
            f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, post in enumerate(posts, 1):
                f.write(f"[포스트 {i}]\n")
                f.write(f"제목: {post.title}\n")
                f.write(f"카테고리: {post.category}\n")
                f.write(f"태그: {', '.join(post.tag) if post.tag else '없음'}\n")
                f.write(f"업로드 시간: {post.upload_hour}시\n")
                f.write("-" * 40 + "\n")
                f.write("내용:\n")
                f.write(post.content)
                f.write("\n\n" + "=" * 80 + "\n\n")
        
        print(f"포스트 미리보기 저장 완료: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")
        return ""
