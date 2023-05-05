import re
import json
import argparse
import logging

logger = logging.getLogger(__name__)

try:
    from yt_dlp import YoutubeDL
except:
    logger.critical(
        "yt-dlp package is required for this fucionality.\n"
        "yt-dlp can be installed via: \n"
        "pip install --upgrade yt-dlp\n"
        "OR\n"
        "pip install --no-deps --upgrade yt-dlp"
    )

regex = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

# pip install --upgrade yt-dlp


def get_arguments():
    parser = argparse.ArgumentParser(
        description=("Prints the chapters of a Youtube video in a simple JSON format.")
    )
    parser.add_argument("id")
    parser.add_argument(
        "-f",
        action="store_true",
        required=False,
        default=False,
        help="Store chapters info in a file with name of the title "
        "and .ch file extension",
    )
    arguments = parser.parse_args()
    return arguments


def make_three_time_tokens(t):
    time_tokens = t.split(":")
    number_of_tokens = len(time_tokens)
    three_token_str = t
    if number_of_tokens == 1:
        three_token_str = f"00:00:{time_tokens[0]}"
    if number_of_tokens == 2:
        three_token_str = f"00:{time_tokens[0]}:{time_tokens[1]}"

    return three_token_str


def make_two_digit_time_tokens(t):
    time_tokens = t.split(":")
    for i, token in enumerate(time_tokens):
        if len(token) == 0:
            time_tokens[i] = "00"
        if len(token) == 1:
            time_tokens[i] = f"0{token}"
    return f"{time_tokens[0]}:{time_tokens[1]}:{time_tokens[2]}"


def get_chapters_from_desc(video_desc):
    chapters_timestamps = {}
    pattern = re.compile(r"((?:(?:[01]?\d|2[0-3]):)?(?:[0-5]?\d):(?:[0-5]?\d)) (.+)")
    for match in pattern.finditer(video_desc):
        chapters_timestamps[match.group(2)] = make_two_digit_time_tokens(
            make_three_time_tokens(match.group(1))
        )
    return chapters_timestamps


def secs_to_hhmmss(secs):
    total_secs = int(secs)
    total_minutes = int(total_secs / 60)
    left_over_secs = total_secs % 60
    hours = int(total_minutes / 60)
    minutes = int(total_minutes % 60)
    seconds = left_over_secs
    sec_s = f"{seconds}" if seconds > 9 else f"0{seconds}"
    min_s = f"{minutes}" if minutes > 9 else f"0{minutes}"
    hr_s = f"{hours}" if hours > 9 else f"0{hours}"
    return f"{hr_s}:{min_s}:{sec_s}"


def get_chapters_from_chapters_entity(video_chapters):
    chapters_timestamps = {}
    for chapter in video_chapters:
        name = chapter["title"]
        tmstamp = chapter["start_time"]
        chapters_timestamps[name] = secs_to_hhmmss(tmstamp)
    return chapters_timestamps


def none_on_exception(f: callable):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(e)
            return None

    return wrapper


@none_on_exception
def get_chapters_json(yt_video: str):
    video_url = None
    if len(yt_video) < 11:
        raise TypeError("Supplied youtube video id or url too short.")
    if isURL(yt_video):
        video_url = yt_video
    else:
        video_url = f"https://youtu.be/{yt_video}"

    with YoutubeDL() as ydl:
        ydl.params["quiet"] = True
        info_dict = ydl.extract_info(video_url, download=False)
    video_title = info_dict.get("title", None)
    video_chapters = info_dict.get("chapters", None)
    chapters_timestamps = {}
    if video_chapters:
        chapters_timestamps = get_chapters_from_chapters_entity(video_chapters)
    else:
        video_desc = info_dict.get("description", None)
        chapters_timestamps = get_chapters_from_desc(video_desc)

    chapters_metadata = {"title": video_title}
    chapters_metadata["chapters"] = chapters_timestamps
    chapters_json_doc = json.dumps(chapters_metadata, indent=4, separators=(",", ": "))
    return video_title, chapters_json_doc


def isURL(in_str):
    if re.match(regex, in_str):
        return True
    else:
        return False


if __name__ == "__main__":
    try:
        type(YoutubeDL)
    except:
        exit()
    prog_args = get_arguments()
    title, json_doc = get_chapters_json(prog_args.id)
    if json_doc:
        if prog_args.f:
            with open(f"{title}.ch", "w+") as f:
                f.write(json_doc)
        else:
            print(json_doc)
