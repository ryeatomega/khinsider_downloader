import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin

initial_page = "https://downloads.khinsider.com/game-soundtracks/album/risk-of-rain-2-survivors-of-the-void-2022"
session = requests.Session()
session.headers["User-Agent"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

download_links = []


def dwnfile(name: str):
    """Function to download the music file

    Args:
        name (str): the link of the file to be downloaded, also used to determine filename
    """
    filename = unquote(name.split("/")[6])
    match input(f"Do you want to download |{filename}| y/n/q?\t").lower():
        case "y":
            print(f"Downloading {filename}")
            response = session.get(name, stream=True)
            response.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                print("Download completed")
        case "n":
            return
        case "q":
            exit(0)
        case _:
            print("Illegal Key Pressed. retry.")
            dwnfile(name)


def main():
    """Main function. it will scrape the initial page and get the list of songs, and go through each one and uses dwnfile() to download them
    """
    init_page = session.get(initial_page)
    init_soup = BeautifulSoup(init_page.text, "html.parser")
    init_td_tags = init_soup.find_all("td", class_="playlistDownloadSong")
    init_a_tags = [a["href"] for td in init_td_tags for a in td.find_all("a")]

    for link in init_a_tags:
        down_page = session.get(urljoin("https://downloads.khinsider.com/", link))
        down_html = down_page.text
        down_soup = BeautifulSoup(down_html, "html.parser")
        for a in down_soup.find_all("a", href=True):
            if a["href"].endswith(".flac"):
                dwnfile(a["href"])


if __name__ == "__main__":
    main()
