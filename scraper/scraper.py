from scraper.exceptions import MissingTagError, ParseError
import itertools
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from collections import namedtuple

"""
UNREVIEWED
WATCHING
COMPLETED
ON_HOLD
DROPPED
PLAN_TO_WATCH
"""

def get_anime(id_ref=1, requester=requests):
    url = get_url_anime(id_ref)

    response = requester.get(url)
    response.raise_for_status()  # May raise
    # TODO: Raise RequestError if 404

    soup = BeautifulSoup(response.content, 'html.parser')
    data = get_anime_data(soup)  # May raise

    meta = {
        'when': datetime.utcnow(),
        'id_ref': id_ref,
        'response': response,
    }
    Retrieved = namedtuple('Retrieved', ['meta', 'data'])
    return Retrieved(meta, data)

def get_url_anime(id):
    # Use HTTPS to avoid auto-redirect from HTTP (except for tests)
    # from .__init__ import _FORCE_HTTP
    # protocol = 'http' if _FORCE_HTTP else 'https'
    protocol = 'https'
    return '{}://myanimelist.net/anime/{:d}'.format(protocol, id)

def _get_name(soup, data=None):
    tag = soup.find('span', itemprop='name')
    if not tag:
        raise MissingTagError('name')

    text = tag.string
    return text

def _get_summary(soup, data=None):
    # for linebreak in soup.find_all('br'):
        # linebreak.extract()
    tag = soup.find('span', itemprop='description')
    # print(tag.string)

    """
    print(soup)
    print(tag.string)
    if not tag:
        raise MissingTagError('name')
    text = tag.string
    return text
    """
    return 'lorem'

def _get_image(soup, data=None):
    tag = soup.find('img', itemprop='image')
    if not tag:
        raise MissingTagError('image')
    text = tag['src']
    return text

def _get_genres(soup, data=None):
    pretag = soup.find('span', string='Genres:')
    if not pretag:
        raise MissingTagError('genres')
    g = pretag.find_next_siblings("a")
    genres = []
    for i in g:
        genres.append(i.string)
    return genres
    """
    for text in itertools.islice(pretag.next_siblings, 3):
        text = text.string.strip()
        if text:
            break
    else:
        text = None
    return text
    """

def _get_format(soup, data=None):
    pretag = soup.find('span', string='Type:')
    # print(pretag.find_next_sibling("a"))
    if not pretag:
        raise MissingTagError('type')

    for text in itertools.islice(pretag.next_siblings, 3):
        text = text.string.strip()
        if text:
            break
    else:
        text = None
    return text
    """
    format_ = Format.mal_to_enum(text)
    if not format_:  # pragma: no cover
        # Either we missed a format, or MAL changed the webpage
        raise ParseError('Unable to identify format from "{}"'.format(text))
    return format_
    """

def _get_episodes(soup, data=None):
    pretag = soup.find('span', string='Episodes:')
    if not pretag:
        raise MissingTagError('episodes')

    episodes_text = pretag.next_sibling.strip().lower()
    if episodes_text == 'unknown':
        return None

    try:
        episodes_number = int(episodes_text)
    except (ValueError, TypeError):  # pragma: no cover
        # MAL probably changed the webpage
        raise ParseError('Unable to convert text "%s" to int' % episodes_text)

    return episodes_number

def _get_airing_status(soup, data=None):
    pretag = soup.find('span', string='Status:')
    if not pretag:
        raise MissingTagError('status')

    status_text = pretag.next_sibling
    """
    status = AiringStatus.mal_to_enum(status_text)

    if not status:  # pragma: no cover
        # MAL probably changed the website
        raise ParseError('Unable to identify airing status from "%s"' % status_text)
    return status
    """
    return status_text

def _get_start_date(soup, data=None):
    pretag = soup.find('span', string='Aired:')
    if not pretag:
        raise MissingTagError('aired')

    aired_text = pretag.next_sibling.strip().lower()
    if aired_text == 'not available':
        return None

    start_text = aired_text.split(' to ')[0]

    try:
        start_date = get_date(start_text)
    except ValueError:  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('Unable to identify date from "%s"' % start_text)

    return start_date

def _get_end_date(soup, data=None):
    pretag = soup.find('span', string='Aired:')
    if not pretag:
        raise MissingTagError('aired')

    aired_text = pretag.next_sibling.strip()
    date_range_text = aired_text.split(' to ')

    # Not all Aired tags have a date range (https://myanimelist.net/anime/5)
    try:
        end_text = date_range_text[1]
    except IndexError:
        return None

    if end_text == '?':
        return None

    try:
        end_date = get_date(end_text)
    except ValueError:  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('Unable to identify date from "%s"' % end_text)

    return end_date

def _get_airing_premiere(soup, data):
    pretag = soup.find('span', string='Premiered:')
    if not pretag:
        # Film: https://myanimelist.net/anime/5
        # OVA: https://myanimelist.net/anime/44
        # ONA: https://myanimelist.net/anime/574
        # TODO: Missing Special
        # Music: https://myanimelist.net/anime/3642
        # Unknown: https://myanimelist.net/anime/33352
        skip = (Format.film, Format.ova, Format.special, Format.ona, Format.music, Format.unknown)
        if data['format'] in skip:
            return None
        else:
            raise MissingTagError('premiered')

    # '?': https://myanimelist.net/anime/3624
    if pretag.next_sibling.string.strip() == '?':
        return None

    season, year = pretag.find_next('a').string.lower().split(' ')

    season = Season.mal_to_enum(season)
    if season is None:
        # MAL probably changed their website
        raise ParseError('Unable to identify season from "%s"' % season)

    try:
        year = int(year)
    except (ValueError, TypeError):  # pragma: no cover
        # MAL probably changed their website
        raise ParseError('Unable to identify year from "%s"' % year)

    return (year, season)

def get_anime_data(soup):
    process = [
        ('name', _get_name),
        ('image', _get_image),
        ('format', _get_format),
        ('genres', _get_genres),
        # ('summary', _get_summary),

        # ('name_english', _get_english_name),
        # ('format', _get_format),
        # ('episodes', _get_episodes),
        # ('airing_status', _get_airing_status),
        # ('airing_started', _get_start_date),
        # ('airing_finished', _get_end_date),
        # ('airing_premiere', _get_airing_premiere),
        # ('mal_age_rating', _get_mal_age_rating),
        # ('mal_score', _get_mal_score),
        # ('mal_scored_by', _get_mal_scored_by),
        # ('mal_rank', _get_mal_rank),
        # ('mal_popularity', _get_mal_popularity),
        # ('mal_members', _get_mal_members),
        # ('mal_favourites', _get_mal_favourites),
    ]
    data = {}
    for tag, func in process:
        try:
            result = func(soup, data)
        except ParseError as err:
            err.specify_tag(tag)
            print('Failed to process tag %s', tag)
            raise

        data[tag] = result
    return data
