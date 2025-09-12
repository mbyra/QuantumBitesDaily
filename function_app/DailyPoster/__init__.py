import logging, datetime
import azure.functions as func
from .shared import generate_copy, generate_background, render_slide, upload_png_and_get_sas, ig_create_image_container, ig_publish_carousel

def main(mytimer: func.TimerRequest) -> None:
    logging.info("QuantumBitesDaily timer fired")
    copy = generate_copy()

    bg1 = generate_background("cosmic, abstract, deep blues and purples, subtle grid, hint of quantum vibe, minimal noise")
    bg2 = generate_background("elegant physics diagram aesthetic, starfield + lines, tasteful, not busy")
    bg3 = generate_background("clean dark cosmic gradient with a subtle rocket or comet trail motif")

    s1 = render_slide(bg1, title=copy["slide1"].splitlines()[0], body="\n".join(copy["slide1"].splitlines()[1:]), slide_no=1)
    s2 = render_slide(bg2, title="More to chew on:", body=copy["slide2"], slide_no=2)
    s3 = render_slide(bg3, title="One more thing…", body=copy["slide3"], slide_no=3)

    date_tag = datetime.datetime.utcnow().strftime("%Y%m%d")
    url1, blob1 = upload_png_and_get_sas(s1, f"{date_tag}_slide1.png")
    url2, blob2 = upload_png_and_get_sas(s2, f"{date_tag}_slide2.png")
    url3, blob3 = upload_png_and_get_sas(s3, f"{date_tag}_slide3.png")

    c1 = ig_create_image_container(url1)
    c2 = ig_create_image_container(url2)
    c3 = ig_create_image_container(url3)

    caption = f"{copy['caption']}\n\n{copy['hashtags']}"
    post_id = ig_publish_carousel([c1,c2,c3], caption)

    logging.info(f"Published carousel post_id={post_id}")