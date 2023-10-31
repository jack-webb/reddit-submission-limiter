
class SubredditConfig:
    def __init__(self, config_dict: dict):
        self.ENABLED: bool = config_dict["enabled"]
        self.PERIOD_HOURS: int = config_dict["period_hours"]
        self.REPORT_ALL: bool = config_dict["report_all"]
        self.SEND_MODMAIL: bool = config_dict["send_modmail"]
        self.REPORT_THRESHOLD: int = config_dict["report_threshold"]
        self.REMOVE_THRESHOLD: int = config_dict["remove_threshold"]
        self.REPORT_MESSAGE: str = config_dict["report_message"]
        self.REMOVE_MESSAGE: str = config_dict["remove_message"]
        self.MODMAIL_SUBJECT: str = config_dict["modmail_subject"]
        self.MODMAIL_MESSAGE: str = config_dict["modmail_message"]
