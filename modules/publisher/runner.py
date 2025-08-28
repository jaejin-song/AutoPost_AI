from . import tistory, x, threads

def publish_all(account_set, blog_post, sns_posts):
    """계정 세트에 맞춰 블로그 + SNS 업로드"""
    print(f"\n=== [{account_set['topic']}] 세트 발행 시작 ===")

    for acc in account_set["accounts"]:
        if acc["platform"] == "tistory":
            tistory.publish(blog_post, acc)
        elif acc["platform"] == "x":
            x.publish(sns_posts["x"], acc)
        elif acc["platform"] == "threads":
            threads.publish(sns_posts["threads"], acc)

    print(f"=== [{account_set['topic']}] 세트 발행 완료 ===\n")
