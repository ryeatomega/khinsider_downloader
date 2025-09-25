import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin

# This is the soundtrack you're gonna download, you should go to their website and search for the OST you want.
initial_page = "https://downloads.khinsider.com/game-soundtracks/album/risk-of-rain-2-survivors-of-the-void-2022"
download_links = []


async def fetch_html(session: aiohttp.ClientSession, link: str) -> str:
    async with session.get(link) as response:
        return await response.text()


async def dwnfile() -> None:
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
                await dwnfile()


async def main():
    global download_links
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }
    ) as global_session:
        init_html = await fetch_html(global_session, initial_page)
        init_soup = BeautifulSoup(init_html, "html.parser")
        init_td_tags = init_soup.find_all("td", class_="playlistDownloadSong")
        init_a_tags = [a["href"] for td in init_td_tags for a in td.find_all("a")]

        for link in init_a_tags:
            down_html = await fetch_html(
                global_session, urljoin("https://downloads.khinsider.com/", link)
            )
            down_soup = BeautifulSoup(down_html, "html.parser")

            for a in down_soup.find_all("a", href=True):
                if a["href"].endswith(".flac"):
                    download_links.append(a["href"])
                    print(download_links)

if __name__ == "__main__":
    asyncio.run(main())
    try:
        asyncio.run(dwnfile())
    except asyncio.CancelledError:
        print("Quitting gracefully")
        exit(0)
