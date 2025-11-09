import asyncio
import aiohttp
import sys
from bs4 import BeautifulSoup, ResultSet
from urllib.parse import unquote, urljoin


async def fetch_html(session: aiohttp.ClientSession, link: str):
    async with session.get(link) as response:
        return BeautifulSoup(await response.text(), "lxml")


async def init_page_scrape(client: aiohttp.ClientSession, init_link: str) -> list[str]:
    print("[INFO] Getting the album page.")
    async with client as global_session:
        soup: BeautifulSoup = await fetch_html(global_session, init_link)
        td_tags: ResultSet = soup.select('td.playlistDownloadSong a[href*=".mp3"]')
        a_tags = [
            urljoin("https://downloads.khinsider.com/", td_tag["href"])
            for td_tag in td_tags
        ]
        print(a_tags)
        return a_tags


async def down_page_scrape(
    client: aiohttp.ClientSession,
    init_content: list[str],
) -> list[str]:
    print("[INFO] Getting track links.")
    async with client as global_session:

        async def process(link):
            down_soup = await fetch_html(global_session, link)
            hrefs = down_soup.select("a:has(span.songDownloadLink)")
            a = next(
                (tag["href"] for tag in hrefs if tag["href"].endswith(".mp3")), None
            )
            return a

        async with asyncio.TaskGroup() as tg:
            tasks: list = [tg.create_task(process(link)) for link in init_content]

    download_links: list[str] = [task.result() for task in tasks]
    return download_links


async def download_list(download_links: list[str]) -> None:
    print("[INFO] Downloading files.")
    for link in download_links:
        filename = unquote(link.split("/")[6])
        while True:
            match input(f"[INFO] Download {filename} [y/n/q]?\n").lower():
                case "y":
                    print(f"[INFO] Downloading {filename}.")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link) as file:
                            file.raise_for_status()
                            with open(filename, "wb") as f:
                                async for chunk in file.content.iter_chunked(8192):
                                    f.write(chunk)
                                print(f"[INFO] Download {filename} completed.")
                    break
                case "n":
                    break
                case "q":
                    raise asyncio.CancelledError()
                case _:
                    print("[ERROR] Invalid option! Try again!", file=sys.stderr)


async def main():
    if len(sys.argv) < 2:
        print("[ERROR] Album link not specified.", file=sys.stderr)
        print("[USAGE] main.py <url>")
    else:
        async with aiohttp.ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            }
        ) as client:
            init_page_content: list[str] = await init_page_scrape(client, sys.argv[1])
            down_page_content: list[str] = await down_page_scrape(
                client, init_page_content
            )
        try:
            asyncio.run(download_list(down_page_content))
        except asyncio.CancelledError:
            print("[INFO] Quitting gracefully.")
            exit(0)


if __name__ == "__main__":
    asyncio.run(main())
