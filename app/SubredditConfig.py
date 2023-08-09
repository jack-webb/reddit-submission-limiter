
class SubredditConfig:
    def __init__(self, config_dict: dict):
        self.enabled: bool = config_dict["enabled"]
        self.period_hours: int = config_dict["period_hours"]
        self.report_all: bool = config_dict["report_all"]
        self.send_modmail: bool = config_dict["send_modmail"]
        self.report_threshold: int = config_dict["report_threshold"]
        self.remove_threshold: int = config_dict["remove_threshold"]
        self.report_message: str = config_dict["report_message"]
        self.remove_message: str = config_dict["remove_message"]
        self.modmail_subject: str = config_dict["modmail_subject"]
        self.modmail_message: str = config_dict["modmail_message"]
