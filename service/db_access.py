from sqlalchemy import false                                 # type: ignore
from sqlalchemy.orm.strategy_options import load_only, Load  # type: ignore
from service import db
from service.models import TitleRegisterData, UprnMapping, UserSearchAndResults


def save_user_search_details(params):
    """
    Save user's search request details, for audit purposes.
    """

    user_search_request = UserSearchAndResults\
                            (
                            viewed_time=params['MC_timestamp'],
                            user_id=params['user_id'],
                            title_number=params['MC_titleNumber'],
                            search_type=params['MC_searchType'],
                            purchase_type=params['MC_purchaseType'],
                            amount=params['amount'],
                            cart_id=params['cartId'],
                            )

    db.session.add(user_search_request)
    db.session.commit()


def get_user_view(user_id, timestamp):
    """
    Get user's view details, after payment.
    """

    view = UserSearchAndResults.query.filter_by(user_id=user_id, viewed_time=timestamp).first()
    return view


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
    amended_lr_uprn = '{' + lr_uprn + '}'
    result = TitleRegisterData.query.options(
        Load(TitleRegisterData).load_only(
            TitleRegisterData.lr_uprns,
            TitleRegisterData.title_number,
            TitleRegisterData.register_data
        )
    ).filter(
        TitleRegisterData.lr_uprns.contains(amended_lr_uprn),
        TitleRegisterData.is_deleted == false()
    ).all()
    if result:
        return result[0]
    else:
        return None


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
