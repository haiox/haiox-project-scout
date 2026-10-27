"""Haiox Project Scout - Ingestion Package."""
from .base import BaseFeedDriver
from .freelancer_driver import FreelancerFeedDriver
from .upwork_driver import UpworkFeedDriver
from .remote_boards_driver import RemoteBoardsDriver
from .local_driver import LocalFeedDriver
from .custom_driver import CustomSiteDriver
from .aggregator import FeedAggregator

__all__ = [
    "BaseFeedDriver",
    "FreelancerFeedDriver",
    "UpworkFeedDriver",
    "RemoteBoardsDriver",
    "LocalFeedDriver",
    "CustomSiteDriver",
    "FeedAggregator",
]
