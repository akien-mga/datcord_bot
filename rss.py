import feedparser
import datetime
import requests

COMMIT_URL = "https://github.com/godotengine/godot/commits/master.atom"
ISSUE_URL = "https://api.github.com/repos/godotengine/godot/issues?sort=created"


class RSSFeed:

    def __init__(self):
        self.commit_url = COMMIT_URL
        self.issue_url = ISSUE_URL

    def parse_commit(self, stamp):
        d = feedparser.parse(self.commit_url)
        if not d.feed.updated == stamp:
            # self.save_stamp("commit", d.feed.updated)
            return d["items"][0], d.feed.updated
        else:
            return None, stamp

    def format_commit_message(self, entry):
        msg = ":outbox_tray: **New commit by {1}:**\n```{0}```\n<{2}>".format(
            entry["title"],
            entry["author"],
            entry["link"]
        )
        return msg

    def check_commit(self, stamp):
        e, newstamp = self.parse_commit(stamp)
        if e:
            return self.format_commit_message(e), newstamp
        else:
            return False, newstamp

    def check_issue(self, stamp):
        try:
            old_stamp = datetime.datetime.strptime(
                stamp,
                "%Y-%m-%dT%H:%M:%SZ"
            )
        except ValueError:
            old_stamp = datetime.datetime.utcnow()
            stamp = datetime.datetime.strftime(
                old_stamp,
                "%Y-%m-%dT%H:%M:%SZ"
            )
        url = "{0}{1}{2}".format(
            self.issue_url, "&since=", stamp
        )
        try:
            r = requests.get(url=url)
        except:
            return [], stamp
        parsed = r.json()

        try:
            r.json()[0]
        except KeyError:
            print("Nothing recieved from API, call limit?")
            return [], stamp    # Probably went over call limit
        except IndexError:
            # No new issues.
            return [], stamp

        # 2016-09-12T20:26:12Z
        messages = []
        latest_stamp = None
        candidate_stamp = old_stamp
        for issue in parsed:
            new_stamp = datetime.datetime.strptime(
                issue["created_at"],
                "%Y-%m-%dT%H:%M:%SZ"
            )
            # print(issue["created_at"], stamp, " | ", old_stamp, new_stamp)
            if new_stamp > old_stamp:
                if new_stamp > candidate_stamp:
                    candidate_stamp = new_stamp
                    latest_stamp = issue["created_at"]
                messages.append(self.format_issue_message(issue))

        if latest_stamp:
            stamp = datetime.datetime.strftime(
                datetime.datetime.utcnow(),
                "%Y-%m-%dT%H:%M:%SZ"
            )

        messages.reverse()
        return messages, stamp

    def format_issue_message(self, e):
        try:
            e["pull_request"]
        except KeyError:
            prefix = ":exclamation: **New issue:**"
        else:
            prefix = ":question: **New pull request:**"
        msg = "{pf} *#{n} by {u}*\n```{t}```\n<{url}>".format(
            pf=prefix,
            n=e["number"],
            u=e["user"]["login"],
            t=e["title"],
            url=e["html_url"]
        )
        return msg


if __name__ == "__main__":
    # For testing
    from time import sleep
    f = RSSFeed()
    while True:
        print(f.check_issue())
        # print(f.check_commit())
        sleep(5)
