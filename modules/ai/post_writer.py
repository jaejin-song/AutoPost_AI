# SNS용 짧은 글 작성

def generate_sns_posts(blog_post):
    print(f"[AI] SNS 글 생성")
    return {
        "x": f"🔥 {blog_post[:20]}... #트렌드",
        "threads": f"💡 {blog_post[:30]}...\n여러분 생각은 어때요?"
    }
