import subprocess
import time

import requests
from bs4 import BeautifulSoup

NOTIFICATION_CMD = """
    on run argv
    display notification (item 3 of argv) with title (item 1 of argv) subtitle (item 2 of argv)
    end run
    """


SCORE_DESCRIPTIONS= {
    "score-w": " Wicket!",
    "score-0": " plays a Dot ball",
    "score-1": " settles for 1 Run",
    "score-2": " gets 2 Runs",
    "score-3": " collects 3 Runs",
    "score-4": " hits a Boundary!",
    "score-6": " just hit a Sixer!",
}


def send_notification(title: str, subtitle: str, text: str) -> None:
    """
    Sends a notification using the osascript command.

    Args:
        title (str): The title of the notification.
        subtitle (str): The subtitle of the notification.
        text (str): The text content of the notification.

    Returns:
        None
    """
    subprocess.call(["osascript", "-e", NOTIFICATION_CMD, title, subtitle, text])


def decipher_score(score):
    map = {
        "LB": " runs with Leg Bye",
        "WD": " runs with a Wide!",
        "NB": " runs with a No Ball!",
    }
    for k, v in map.items():
        score = score.replace(k, v)
        break
    return score


def main():
    """
    Main function to monitor live cricket match commentary and send notifications.
    """
    current_ball_number = ""
    previous_match_status = ""
    current_match_status = ""

    print("\n\n")
    print("This is Cricket Live Score Monitor Utility for MacOS")
    print(
        "Browse to https://sportzwiki.com/ and find the live match you want to follow"
    )
    print("Once found, enter the url in the prompt below\n")
    LIVE_SCORE_URL = input("Enter the sportzwiki url for the live match: ")
    print(
        "\nYou can now minimize this window, you will get ball by ball updates of the match in your MacOS notifications"
    )
    page = requests.get(LIVE_SCORE_URL)
    soup = BeautifulSoup(page.content, "html.parser")
    team_a_name = soup.find(class_="teama").find(class_="teamAbbr").text
    team_b_name = soup.find(class_="teamb").find(class_="teamAbbr").text
    while True:
        try:
            page = requests.get(LIVE_SCORE_URL)
            soup = BeautifulSoup(page.content, "html.parser")

            current_match_status = soup.find(class_="status_note").text
            team_a_score = soup.find(class_="teamaScore").text
            team_b_score = soup.find(class_="teambScore").text
            if not team_b_score:
                current_score = f"{team_a_name}: {team_a_score}"
            else:
                current_score = (
                    f"{team_a_name}: {team_a_score} | {team_b_name}: {team_b_score}"
                )

            if previous_match_status != current_match_status:
                previous_match_status = current_match_status
                if ":" in current_match_status:
                    heading, text = current_match_status.split(":")
                else:
                    heading, text = (
                        " vs ".join([team_a_name, team_b_name]),
                        current_match_status,
                    )
                send_notification(heading, text, current_score)
                if any(
                    end_case in current_match_status for end_case in ["won by", "draw"]
                ):
                    break
                time.sleep(3)

            commentary_div = soup.find(class_="commentaries")
            latest_commentary = (
                commentary_div.findChildren()[1]
                if len(commentary_div.findChildren()) > 1
                else None
            )

            if latest_commentary and "comment-overend" in latest_commentary.attrs.get(
                "class", []
            ):
                latest_commentary = commentary_div.find(class_="score").parent

            if latest_commentary:
                if current_ball_number != latest_commentary.find(class_="ovb").text:
                    current_ball_number = latest_commentary.find(class_="ovb").text
                    commentary_text = latest_commentary.find(class_="text").text
                    commentary_text = commentary_text[: commentary_text.index(",")]
                    _, batsman = commentary_text.split(" to ")
                    score_element = latest_commentary.find(class_="score")
                    score_value = score_element.attrs["class"][-1]
                    score_description = SCORE_DESCRIPTIONS.get(
                        score_value, score_value.replace("score-", "").upper()
                    )
                    score_description = (
                        f"{batsman.strip()} {decipher_score(score_description)}"
                        if "Wicket" not in score_description
                        else score_description
                    )
                    send_notification(score_description, commentary_text, current_score)

            time.sleep(5)

        except Exception as e:
            print(e)
            continue


if __name__ == "__main__":
    main()
