from sqlalchemy import false                                 # type: ignore
from sqlalchemy.orm.strategy_options import load_only, Load  # type: ignore

from service.models import TitleRegisterData, UprnMapping


def get_title_register(title_number):
    # TODO: trust our own code to do the right thing - validate data on input instead
    if title_number:
        # Will retrieve the first matching title that is not marked as deleted
        result = TitleRegisterData.query.options(
            Load(TitleRegisterData).load_only(
                TitleRegisterData.title_number.name,
                TitleRegisterData.register_data.name,
                TitleRegisterData.geometry_data.name
            )
        ).filter(
            TitleRegisterData.title_number == title_number,
            TitleRegisterData.is_deleted == false()
        ).first()

        return result
    else:
        raise TypeError('Title number must not be None.')


def get_title_registers(title_numbers):
    # Will retrieve matching titles that are not marked as deleted
    fields = [TitleRegisterData.title_number.name, TitleRegisterData.register_data.name,
              TitleRegisterData.geometry_data.name]
    query = TitleRegisterData.query.options(Load(TitleRegisterData).load_only(*fields))
    results = query.filter(TitleRegisterData.title_number.in_(title_numbers),
                           TitleRegisterData.is_deleted == false()).all()
    return results


def get_official_copy_data(title_number):
    result = TitleRegisterData.query.options(
        Load(TitleRegisterData).load_only(
            TitleRegisterData.title_number.name,
            TitleRegisterData.official_copy_data.name
        )
    ).filter(
        TitleRegisterData.title_number == title_number,
        TitleRegisterData.is_deleted == false()
    ).first()

    return result


def get_title_number_and_register_data(lr_uprn):
    result = TitleRegisterData.query.options(
        Load(TitleRegisterData).load_only(
            TitleRegisterData.lr_uprns,
            TitleRegisterData.title_number,
            TitleRegisterData.register_data
        )
    ).filter(
        TitleRegisterData.lr_uprns.any(lr_uprn),
        TitleRegisterData.is_deleted == false()
    ).first()

    return result

def get_mapped_lruprn(address_base_uprn):
        result = UprnMapping.query.options(
            Load(UprnMapping).load_only(
                UprnMapping.lr_uprn.name,
                UprnMapping.uprn.name
            )
        ).filter(
            UprnMapping.uprn == address_base_uprn
        ).first()

        return result
