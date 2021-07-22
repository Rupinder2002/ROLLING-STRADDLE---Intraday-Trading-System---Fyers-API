import pendulum
from pendulum.date import Date

listOfNseHolidays = set([
    Date(2021, 1, 26),  # Republic Day
    Date(2021, 3, 11),  # Maha Shivaratri
    Date(2021, 3, 29),  # Holi
    Date(2021, 4, 2),  # Good Friday
    Date(2021, 4, 14),  # Dr.Baba Saheb Ambedkar Jayanti
    Date(2021, 4, 21),  # Ram Navami
    Date(2021, 5, 13),  # Id-ul-Fitr
    Date(2021, 7, 21),  # Id-al-Adha
    Date(2021, 8, 19),  # Ashura
    Date(2021, 9, 10),  # Ganesh Chaturthi
    Date(2021, 10, 15),  # Vijaya Dashami
    Date(2021, 11, 5),  # Diwali/Laxmi Puja
    Date(2021, 11, 19)   # Guru Nanak Jayanti
])

def getNearestWeeklyExpiryDate():
    expiryDate = None
    if(pendulum.now().date().day_of_week is pendulum.THURSDAY):
        expiryDate = pendulum.now()
    else:
        expiryDate = pendulum.now().next(pendulum.THURSDAY)
    return __considerHolidayList(expiryDate).date()


def getNextWeeklyExpiryDate():
    expiryDate = None
    if(pendulum.now().date().day_of_week is pendulum.THURSDAY):
        expiryDate = pendulum.now().next(pendulum.THURSDAY)
    else:
        expiryDate = pendulum.now().next(pendulum.THURSDAY).next(pendulum.THURSDAY)
    return __considerHolidayList(expiryDate).date()


def getNearestMonthlyExpiryDate():
    expiryDate = pendulum.now().last_of('month', pendulum.THURSDAY)
    if(pendulum.now().date() > expiryDate.date()):
        expiryDate = pendulum.now().add(months=1).last_of('month', pendulum.THURSDAY)
    return __considerHolidayList(expiryDate).date()


def getNextMonthlyExpiryDate():
    expiryDate = pendulum.now().last_of('month', pendulum.THURSDAY)
    if(pendulum.now().date() > expiryDate.date()):
        expiryDate = pendulum.now().add(months=2).last_of('month', pendulum.THURSDAY)
    else:
        expiryDate = pendulum.now().add(months=1).last_of('month', pendulum.THURSDAY)
    return __considerHolidayList(expiryDate).date()


# utility method to be used only by this module
def __considerHolidayList(expiryDate: Date):
    if(expiryDate.date() in listOfNseHolidays):
        return __considerHolidayList(expiryDate.subtract(days=1))
    else:
        return expiryDate

# print('today is '+str(pendulum.now().date()))
# print('nearest weekly exp is '+str(getNearestWeeklyExpiryDate()))
# print('next weekly exp is '+str(getNextWeeklyExpiryDate()))
# print('nearest monthly exp is '+str(getNearestMonthlyExpiryDate()))
# print('next month exp is '+str(getNextMonthlyExpiryDate()))