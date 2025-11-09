import asyncio
import aiohttp
from bs4 import BeautifulSoup, ResultSet, Tag
from urllib.parse import unquote, urljoin

# This is the soundtrack you're gonna download, you should go to their website and search for the OST you want.
ost_link = "https://downloads.khinsider.com/game-soundtracks/album/risk-of-rain-2-survivors-of-the-void-2022"


async def find_flac_link(tags: ResultSet[Tag]) -> str:
    for tag in tags:
        href = tag["href"]
        if href.endswith(".flac"):
            return href


async def fetch_html(session: aiohttp.ClientSession, link: str):
    async with session.get(link) as response:
        return BeautifulSoup(await response.text(), "lxml")


async def init_page_scrape(init_link: str) -> list[str]:
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }
    ) as global_session:
        soup = await fetch_html(global_session, init_link)
        td_tags = soup.select('td.playlistDownloadSong a[href*=".mp3"]')
        a_tags = [
            urljoin("https://downloads.khinsider.com/", a_tag["href"])
            for a_tag in td_tags
        ]
        print(a_tags)

        return a_tags


async def down_page_scrape(init_content: list[str]) -> list[str]:
    download_links = []
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }
    ) as global_session:

        async def process(link):
            down_soup = await fetch_html(global_session, link)
            hrefs = down_soup.select("a:has(span.songDownloadLink)")
            return await find_flac_link(hrefs)

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(process(link)) for link in init_content]

    download_links = [task.result() for task in tasks]
    return download_links


async def download_list(download_links: list[str]) -> None:
    for link in download_links:
        filename = unquote(link.split("/")[6])
        match input(f"Do you want to download |{filename}| y/n/q? ").lower():
            case "y":
                print(f"Downloading {filename}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(link) as file:
                        file.raise_for_status()
                        with open(filename, "wb") as f:
                            async for chunk in file.content.iter_chunked(8192):
                                f.write(chunk)
                            print("Download completed")
            case "n":
                continue
            case "q":
                raise asyncio.CancelledError()
            case _:
                print("Illegal Key Pressed. retry.")
                await download_list()


if __name__ == "__main__":
    init_page_content: list[str] = asyncio.run(init_page_scrape(ost_link))
    down_page_content: list[str] = asyncio.run(down_page_scrape(init_page_content))
    print(down_page_content)
    try:
        asyncio.run(download_list(down_page_content))
    except asyncio.CancelledError:
        print("Quitting gracefully.")
        exit(0)
