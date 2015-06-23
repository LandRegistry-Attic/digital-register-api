from sqlalchemy import false
from service.models import TitleRegisterData


# TODO: write integration tests
def get_title_register(title_ref):
    if title_ref:
        # Will retrieve the first matching title that is not marked as deleted
        result = TitleRegisterData.query.filter(TitleRegisterData.title_number == title_ref,
                                                TitleRegisterData.is_deleted == false()).first()
        return result
    else:
        raise TypeError('Title number must not be None.')
