from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Label import Label
from Tools.LoadPixmap import LoadPixmap
import re
import pickle
from datetime import datetime, timedelta
import os
import time
from enigma import eTimer
import logging

try:
    import requests
except ImportError:
    requests = None

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/ciefp_mojtv_epg.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PLUGIN_VERSION = "1.3"

class MainScreen(Screen):
    skin = """
    <screen name="CiefpMojTvEPG" position="center,center" size="1800,800" title="..:: CiefpMojTvEPG ::..">
        <widget name="channel_list" position="10,10" size="400,627" scrollbarMode="showAlways" itemHeight="33" font="Regular;28" />
        <widget name="epg_list" position="420,10" size="1360,627" scrollbarMode="showAlways" itemHeight="33" font="Regular;28" />
        <widget name="channel_logo" position="10,660" size="220,132" alphatest="on" />
        <widget name="plugin_logo" position="240,660" size="220,132" alphatest="on" />
        <widget name="error_label" position="420,360" size="1160,80" font="Regular;30" halign="center" valign="center" transparent="1" />
        <widget name="plugin2_logo" position="450,660" size="1350,132" alphatest="on" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["channel_list"] = MenuList([], enableWrapAround=True)
        self["epg_list"] = MenuList([], enableWrapAround=True)
        self["channel_logo"] = Pixmap()
        self["plugin_logo"] = Pixmap()
        self["plugin2_logo"] = Pixmap()
        self["error_label"] = Label("")
        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"],
            {
                "ok": self.toggleFocus,
                "cancel": self.close,
                "up": self.moveUp,
                "down": self.moveDown
            }, -2)
        self.channels = [
            ("RTS1", "33.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=33", "33"),
            ("RTS2", "34.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=34", "34"),
            ("RTS3", "443.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=443", "443"),
            ("RTS SAT", "65.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=65", "65"),
            ("RTV1", "182.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=182", "182"),
            ("RTV2", "183.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=183", "183"),
            ("NovaS", "643.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=643", "643"),
            ("B92", "31.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=31", "31"),
            ("PINK", "27.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=27", "27"),
            ("Pink Plus", "29.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=29", "29"),
            ("PRVA", "38.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=38", "38"),
            ("PRVA PLUS", "408.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=408", "408"),
            ("Prva Max", "534.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=534", "534"),
            ("Prva World", "535.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=535", "535"),
            ("Prva Kick", "637.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=637", "637"),
            ("Prva Files", "644.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=644", "644"),
            ("Prva Life", "642.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=642", "642"),
            ("RED TV", "391.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=391", "391"),
            ("Grand", "456.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=456", "456"),
            ("HRT1", "1.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=1", "1"),
            ("HRT2", "2.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=2", "2"),
            ("HRT3", "310.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=310", "310"),
            ("Nova TV", "3.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=3", "3"),
            ("RTL", "4.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=4", "4"),
            ("BHT1", "24.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=24", "24"),
            ("Federalna TV", "25.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=25", "25"),
            ("OBN", "26.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=26", "26"),
            ("Nova BH", "28.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=28", "28"),
            ("HAYAT", "35.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=35", "35"),
            ("RTRS", "36.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=36", "36"),
            ("TV Slovenija1", "19.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=19", "19"),
            ("TV Slovenija2", "20.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=20", "20"),
            ("TV Slovenija3", "221.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=221", "221"),
            ("POP TV", "17.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=17", "17"),
            ("Kanal A", "18.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=18", "18"),
            ("Kino", "273.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=273", "273"),
            ("RTCG1", "173.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=173", "173"),
            ("RTCG2", "174.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=174", "174"),
            ("Cinemania", "30.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=30", "30"),
            ("HBO", "366.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=366", "366"),
            ("HBO2", "367.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=367", "367"),
            ("HBO3", "515.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=515", "515"),
            ("Cinemax", "368.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=368", "368"),
            ("Cinemax2", "369.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=369", "369"),
            ("Cinestar Fantasy", "600.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=600", "600"),
            ("Travel", "486.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=486", "486"),
            ("TLC", "487.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=487", "487"),
            ("Discovery Channel", "488.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=488", "488"),
            ("Animal Planet", "489.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=489", "489"),
            ("Investigation Discovery", "256.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=256", "256"),
            ("Viasat History", "379.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=379", "379"),
            ("Viasat Explore", "380.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=380", "380"),
            ("Pink Pedia", "426.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=426", "426"),
            ("Dox TV", "699.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=699", "699"),
            ("MTV", "165.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=165", "165"),
            ("MTV Hits", "46.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=46", "46"),
            ("Mezzo", "227.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=227", "227"),
            ("Cartoon Network ", "248.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=248", "248"),
            ("Nickelodeon", "88.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=88", "88"),
            ("Mini TV", "89.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=89", "89"),
            ("Pink Kids", "411.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=411", "411"),
            ("Pink Super Kids", "469.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=469", "469"),
            ("Da Vinci Learning", "269.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=269", "269"),
            ("Das Erste HD", "170.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=170", "170"),
            ("Arena Sport Premium 1", "719.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=719", "719"),
            ("Arena Sport Premium 2", "720.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=720", "720"),
            ("Arena Sport Premium 3", "721.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=721", "721"),
            ("Arena Sport 1", "349.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=349", "349"),
            ("Arena Sport 2", "350.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=350", "350"),
            ("Arena Sport 3", "351.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=351", "351"),
            ("Arena Sport 4", "352.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=352", "352"),
            ("Arena Sport 5", "398.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=398", "398"),
            ("Arena Sport 6", "710.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=710", "710"),
            ("Arena Sport 7", "711.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=711", "711"),
            ("Arena Sport 8", "712.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=712", "712"),
            ("Eurosport 1", "493.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=493", "493"),
            ("Eurosport 2", "494.png", "https://mojtv.hr/m2/tv-program/kanal.aspx?id=494", "494"),
        ]
        self.focus_on_channels = True
        self.picon_dir = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpMojTvEPG/picon"
        self.placeholder_icon = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpMojTvEPG/picon/placeholder.png"
        self.plugin_icon = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpMojTvEPG/picon/plugin.png"
        self.plugin2_icon = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpMojTvEPG/picon/plugin2.png"
        self.tmp_dir = "/tmp/CiefpMojTvEPG"
        
        if requests is None:
            self["error_label"].setText("Error: python3-requests is not installed!")
            logger.error("python3-requests is not installed!")
            return

        # Create picon directory if it doesn't exist
        if not os.path.exists(self.picon_dir):
            try:
                os.makedirs(self.picon_dir)
                logger.debug(f"Created picon directory: {self.picon_dir}")
            except Exception as e:
                logger.error(f"Error creating picon directory: {str(e)}")
                self["error_label"].setText(f"Error creating picon directory: {str(e)}")
                return

        # Create tmp directory if it doesn't exist
        if not os.path.exists(self.tmp_dir):
            try:
                os.makedirs(self.tmp_dir)
                logger.debug(f"Created tmp directory: {self.tmp_dir}")
            except Exception as e:
                logger.error(f"Error creating tmp directory: {str(e)}")
                self["error_label"].setText(f"Error creating tmp directory: {str(e)}")
                return

        self.loadChannels()
        self.downloadLogos()
        self.initTimer = eTimer()
        self.initTimer.callback.append(self.delayedInit)
        self.initTimer.start(100, True)

    def delayedInit(self):
        try:
            self.updateEPG()
            self.updatePluginLogo()
            self.updatePlugin2Logo()
        except Exception as e:
            logger.error(f"Error in delayedInit: {str(e)}")
            self["error_label"].setText(f"Error initializing EPG: {str(e)}")

    def loadChannels(self):
        logger.debug("Loading channels...")
        self["channel_list"].setList([x[0] for x in self.channels])
        logger.debug(f"Channels loaded: {[x[0] for x in self.channels]}")

    def downloadLogos(self):
        logger.debug("Downloading logos...")
        for channel in self.channels:
            logo_path = os.path.join(self.picon_dir, channel[1])
            if not os.path.exists(logo_path):
                try:
                    logo_url = f"https://mojtv.hr/m2/img/ch/{channel[3]}.png"
                    response = requests.get(logo_url)
                    response.raise_for_status()
                    with open(logo_path, "wb") as f:
                        f.write(response.content)
                    logger.debug(f"Logo downloaded for {channel[0]}: {logo_path}")
                except Exception as e:
                    logger.warning(f"Error downloading logo for {channel[0]}: {str(e)}")

    def updateLogo(self):
        selected_channel = self["channel_list"].getCurrent()
        if not selected_channel:
            logger.debug("No channel selected")
            return
        for channel in self.channels:
            if channel[0] == selected_channel:
                logo_path = os.path.join(self.picon_dir, channel[1])
                pixmap = None
                if os.path.exists(logo_path):
                    pixmap = LoadPixmap(logo_path)
                    if pixmap:
                        logger.debug(f"Successfully loaded logo: {logo_path}")
                    else:
                        logger.warning(f"Failed to load pixmap for logo: {logo_path}")
                else:
                    if os.path.exists(self.placeholder_icon):
                        pixmap = LoadPixmap(self.placeholder_icon)
                        if pixmap:
                            logger.debug(f"Successfully loaded placeholder icon: {self.placeholder_icon}")
                        else:
                            logger.warning(f"Failed to load pixmap for placeholder icon: {self.placeholder_icon}")
                    else:
                        logger.warning(f"Logo not found: {logo_path}, placeholder icon also missing: {self.placeholder_icon}")
                
                if pixmap and self["channel_logo"].instance:
                    try:
                        self["channel_logo"].instance.setPixmap(pixmap)
                        logger.debug(f"Channel logo set for {channel[0]}: {logo_path}")
                    except Exception as e:
                        logger.error(f"Error setting channel logo for {channel[0]}: {str(e)}")
                else:
                    logger.debug(f"Channel logo widget not initialized or pixmap not loaded for {channel[0]}")
                break

    def updatePluginLogo(self):
        pixmap = None
        if os.path.exists(self.plugin_icon):
            pixmap = LoadPixmap(self.plugin_icon)
            if pixmap:
                logger.debug(f"Successfully loaded plugin logo: {self.plugin_icon}")
            else:
                logger.warning(f"Failed to load pixmap for plugin logo: {self.plugin_icon}")
        else:
            logger.warning(f"Plugin logo not found: {self.plugin_icon}")
        
        if pixmap and self["plugin_logo"].instance:
            try:
                self["plugin_logo"].instance.setPixmap(pixmap)
                logger.debug(f"Plugin logo set: {self.plugin_icon}")
            except Exception as e:
                logger.error(f"Error setting plugin logo: {str(e)}")
        else:
            logger.debug(f"Plugin logo widget not initialized or pixmap not loaded")

    def updatePlugin2Logo(self):
        pixmap = None
        if os.path.exists(self.plugin2_icon):
            pixmap = LoadPixmap(self.plugin2_icon)
            if pixmap:
                logger.debug(f"Successfully loaded plugin2 logo: {self.plugin2_icon}")
            else:
                logger.warning(f"Failed to load pixmap for plugin2 logo: {self.plugin2_icon}")
        else:
            logger.warning(f"Plugin2 logo not found: {self.plugin2_icon}")
        
        if pixmap and self["plugin2_logo"].instance:
            try:
                self["plugin2_logo"].instance.setPixmap(pixmap)
                logger.debug(f"Plugin2 logo set: {self.plugin2_icon}")
            except Exception as e:
                logger.error(f"Error setting plugin2 logo: {str(e)}")
        else:
            logger.debug(f"Plugin2 logo widget not initialized or pixmap not loaded")

    def fetchEPG(self, url, channel_id):
        cache_file = os.path.join(self.tmp_dir, f"epg_{channel_id}.cache")
        if os.path.exists(cache_file):
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age > 3600:
                logger.debug(f"Cache for {channel_id} is too old, deleting: {cache_file}")
                os.remove(cache_file)
            else:
                try:
                    with open(cache_file, "r") as f:
                        data = eval(f.read())
                        if data and isinstance(data, list):
                            logger.debug(f"Loading EPG from cache for {channel_id}: {cache_file}")
                            return data
                        else:
                            logger.debug(f"Invalid or empty cache for {channel_id}, deleting: {cache_file}")
                            os.remove(cache_file)
                except Exception as e:
                    logger.error(f"Error reading cache for {channel_id}: {str(e)}")
                    os.remove(cache_file)

        try:
            logger.debug(f"Fetching EPG from {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            html_file = os.path.join(self.tmp_dir, f"html_{channel_id}.txt")
            with open(html_file, "w") as f:
                f.write(html)
            epg_list = []
            now = datetime.now()
            regex_patterns = {
                'sport_channels': r'<span class="show-time"[^>]*><b>(\d{2}:\d{2})</b></span>.*?<span style="font-size:16px; white-space:normal"><b>([^<]+)</b>.*?(?:<em[^>]*>(.*?)</em>|<span style=\'font-size:14px;[^>]*>(.*?)</span>)?',
                'default': r'<span class="show-time"[^>]*><b>(\d{2}:\d{2})</b></span>.*?<span style="font-size:16px; white-space:normal"><b>([^<]+)</b>.*?(?:<em[^>]*>(.*?)</em>|<span style=\'font-size:14px;[^>]*>(.*?)</span>)?'
            }
            selected_channel = self["channel_list"].getCurrent()
            pattern = regex_patterns['sport_channels'] if selected_channel and ('Arena Sport' in selected_channel or 'Eurosport' in selected_channel) else regex_patterns['default']
            program_rows = re.findall(pattern, html, re.DOTALL)
            logger.debug(f"Regex matches for channel {channel_id}: {program_rows}")
            for time_str, title, em_desc, span_desc in program_rows:
                try:
                    start_time = datetime.strptime(time_str, "%H:%M")
                    start_time = start_time.replace(year=now.year, month=now.month, day=now.day)
                    description = em_desc or span_desc or "No description available"
                    epg_list.append({
                        "start": time_str,
                        "title": title.strip(),
                        "description": description.strip() or "No description available"
                    })
                except ValueError:
                    continue
            if epg_list:
                logger.debug(f"Found {len(epg_list)} EPG entries")
                with open(cache_file, "w") as f:
                    f.write(str(epg_list))
            else:
                logger.debug("No EPG entries found")
                self["error_label"].setText("No EPG data available!")
            return epg_list
        except Exception as e:
            logger.error(f"Error fetching EPG for {channel_id}: {str(e)}")
            self["error_label"].setText(f"Error: {str(e)}")
            return []

    def updateEPG(self):
        selected_channel = self["channel_list"].getCurrent()
        if not selected_channel:
            logger.debug("No channel selected")
            self["error_label"].setText("No channel selected!")
            self["epg_list"].setList([])  # Clear EPG list
            return
        for channel in self.channels:
            if channel[0] == selected_channel:
                logger.debug(f"Updating EPG for {channel[0]}...")
                cache_file = os.path.join(self.tmp_dir, f"epg_{channel[3]}.cache")
                epg_data = self.fetchEPG(channel[2], channel[3])
                self["epg_list"].setList([f"{x['start']} - {x['title']} - {x['description']}" for x in epg_data])
                logger.debug(f"EPG loaded for {channel[0]}: {len(epg_data)} entries")
                if epg_data:
                    self["error_label"].setText("")  # Clear error message on success
                    # Set focus to the currently airing program
                    now = datetime.now()
                    current_index = 0
                    for index, epg_entry in enumerate(epg_data):
                        start_time = epg_entry['start']
                        try:
                            start_dt = datetime.strptime(start_time, "%H:%M")
                            start_dt = start_dt.replace(year=now.year, month=now.month, day=now.day)
                            # Assume a program duration (e.g., 1 hour) since end time isn't provided
                            end_dt = start_dt + timedelta(hours=1)
                            if start_dt <= now <= end_dt:
                                current_index = index
                                logger.debug(f"Found currently airing program at index {current_index}: {epg_entry['start']} - {epg_entry['title']}")
                                break
                        except ValueError:
                            continue
                    self["epg_list"].moveToIndex(current_index)
                    logger.debug(f"EPG selection set to index {current_index} for channel {channel[0]}")
                else:
                    self["error_label"].setText("No EPG data available!")
                self.updateLogo()
                break
        else:
            logger.debug(f"Channel {selected_channel} not found in channel list")
            self["error_label"].setText("Selected channel not found!")
            self["epg_list"].setList([])  # Clear EPG list

    def toggleFocus(self):
        self.focus_on_channels = not self.focus_on_channels
        self["channel_list"].instance.setSelectionEnable(self.focus_on_channels)
        self["epg_list"].instance.setSelectionEnable(not self.focus_on_channels)
        logger.debug(f"Focus switched to {'channels' if self.focus_on_channels else 'EPG'}")
        if self.focus_on_channels:
            self.updateEPG()
        else:
            # When switching to EPG, select the currently airing program
            epg_list = self["epg_list"].getList()
            if epg_list:
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                current_index = 0
                for index, epg_entry in enumerate(epg_list):
                    start_time = epg_entry.split(" - ")[0]
                    try:
                        start_dt = datetime.strptime(start_time, "%H:%M")
                        start_dt = start_dt.replace(year=now.year, month=now.month, day=now.day)
                        # Assume a program duration (e.g., 1 hour) since end time isn't provided
                        end_dt = start_dt + timedelta(hours=1)
                        if start_dt <= now <= end_dt:
                            current_index = index
                            logger.debug(f"Found currently airing program at index {current_index}: {epg_entry}")
                            break
                    except ValueError:
                        continue
                self["epg_list"].moveToIndex(current_index)
                logger.debug(f"EPG selection set to index {current_index}")

    def moveUp(self):
        if self.focus_on_channels:
            self["channel_list"].up()
            self.updateEPG()
            logger.debug("Moved up in channel list")
        else:
            self["epg_list"].up()
            logger.debug("Moved up in EPG list")

    def moveDown(self):
        if self.focus_on_channels:
            self["channel_list"].down()
            self.updateEPG()
            logger.debug("Moved down in channel list")
        else:
            self["epg_list"].down()
            logger.debug("Moved down in EPG list")

def main(session, **kwargs):
    session.open(MainScreen)

def Plugins(**kwargs):
    return PluginDescriptor(
        name="CiefpMojTvEPG",
        description=f"EPG plugin using MojTV data (Version {PLUGIN_VERSION})",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon="icon.png",
        fnc=main
    )