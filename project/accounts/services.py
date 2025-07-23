"""
Contains functions and classes that conduct the business logic of the application
that is too complex to be performed in a serializer or view/viewset.
"""
from datetime import datetime, timezone, timedelta
from enum import Enum
from django.http import HttpRequest
from .models import ExtendedUser, Follow, FollowRequest


def get_current_user_from_request(request: HttpRequest) -> ExtendedUser:
    """
    Returns the `ExtendedUser` currently logged in.
    """
    return ExtendedUser.objects.get(user=request.user)


class ISOWeekday(Enum):
    """
    Official numbers used for each weekday by the 
    International Organization for Standardization (ISO).
    """
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class DateManager:
    """
    Function class that provides information about the current datetime
    as necessary to control the recurring opening/closing of the app
    and to filter what content is shown.
    """


    @staticmethod
    def _get_day_at(utc_offset: int) -> ISOWeekday:
        # Returns ISO number for day of the week at the timezone defined by `utc_offset`
        current_datetime = datetime.now(tz=timezone(timedelta(hours=utc_offset)))
        current_weekday = ISOWeekday(current_datetime.date().isoweekday())
        return current_weekday

    @staticmethod
    def is_sunday() -> bool:
        """
        Returns `True` if it is currently Sunday anywhere on Earth.
        """
        kiribati_day = DateManager._get_day_at(+14)
        idlw_day = DateManager._get_day_at(-12)
        return kiribati_day == ISOWeekday.SUNDAY or idlw_day == ISOWeekday.SUNDAY


    class Countdown:
        """
        To represent the amount of time left until the next time the platform is open.
        DOES NOT AUTOMATICALLY UPDATE. The time left until the platform is next open
        is captured at the moment of instantiation, and does not automatically decrement itself.
        """
        def __init__(self, days: int, hours: int, minutes: int):
            self.days = days
            self.hours = hours
            self.minutes = minutes

        def is_zero(self) -> bool:
            """
            Returns `True` if there is no time left in the countdown.
            """
            return self.days == 0 and self.hours == 0 and self.minutes == 0

        @staticmethod
        def to_next_sunday() -> "DateManager.Countdown":
            """
            Returns a `Countdown` representing the amount of time until it is Sunday 
            anywhere on Earth. If it is currently Sunday anywhere on Earth, 
            returns a timedelta of 0.
            """
            if DateManager.is_sunday():
                return DateManager.Countdown(0, 0, 0)
            else:
                kiribati_tz = timezone(offset=timedelta(hours=+14))
                kiribati_now = datetime.now(tz=kiribati_tz)
                # Find how many days until next sunday
                kiritbati_days_until_sunday: int = 7 - kiribati_now.weekday()
                # Add that to the beginning of today to find the beginning of next sunday
                kiribati_beginning_of_today = datetime(
                    kiribati_now.year,
                    kiribati_now.month, 
                    kiribati_now.day, 
                    0, 0, 0,
                    tzinfo=kiribati_tz
                )
                kiribati_beginning_of_next_sunday: datetime = \
                    kiribati_beginning_of_today \
                    + timedelta(days=kiritbati_days_until_sunday)
                # Subtract today to find the time until the beginning of next sunday
                timedelta_to_next_sunday: timedelta = kiribati_beginning_of_next_sunday - kiribati_now

                # Extract days, minutes, and seconds from the `timedelta`.
                # str() method of `timedelta` returns 'day(s), h:m:s.ms'
                countdown_days: int = timedelta_to_next_sunday.days
                countdown_fraction_of_day: timedelta = timedelta_to_next_sunday - timedelta(days=countdown_days)
                countdown_hours = countdown_fraction_of_day.seconds // (60 * 60)
                countdown_minutes = (countdown_fraction_of_day.seconds // 60) % 60
                return DateManager.Countdown(countdown_days, countdown_hours, countdown_minutes)

        def to_dict(self) -> dict[str, int]:
            """
            Returns this `Countdown` serialized as a JSON string.
            """
            return {
                "days": self.days,
                "hours": self.hours,
                "minutes": self.minutes
            }


    @staticmethod
    def last_sunday() -> datetime:
        """
        Returns a datetime representing the beginning of the last Sunday in Kiribati.
        If it is currently Sunday, returns the beginning of today in Kiribati.
        """
        kiribati_tz = timezone(offset=timedelta(hours=+14))
        kiribati_now = datetime.now(tz=kiribati_tz)
        kiribati_beginning_of_today: datetime = datetime(
            kiribati_now.year,
            kiribati_now.month, 
            kiribati_now.day, 
            0, 0, 0,
            tzinfo=kiribati_tz
        )
        if DateManager.is_sunday():
            return kiribati_beginning_of_today
        else:
            # Find how many days in Kiribati since it was last sunday
            kiritbati_days_since_sunday: int = kiribati_now.weekday()
            return kiribati_beginning_of_today - timedelta(days=kiritbati_days_since_sunday)
        
class FollowService:
    """
    Methods and classes to manage follower-followee relationships and follow requests.
    """

    class AlreadyFollowingException(Exception):
        message = "User already follows the requested user."
        def __init__(self):
            super().__init__(self.message)

    class AlreadyRequestedException(Exception):
        message = "User already has a pending request to follow the requested user."
        def __init__(self):
            super().__init__(self.message)
        
    @staticmethod
    def create_request(follower: ExtendedUser, followee: ExtendedUser) -> None:
        # Do not create a follow request if follower already following followee
        if Follow.objects.filter(follower=follower, followee=followee).exists():
            raise FollowService.AlreadyFollowingException()
        
        # Custom error for when repeat requests are attempted
        if FollowRequest.objects.filter(follower=follower, followee=followee).exists():
            raise FollowService.AlreadyRequestedException()
        
        FollowRequest.objects.create(follower=follower, followee=followee)