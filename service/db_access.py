import hashlib
from sqlalchemy import false                                 # type: ignore
from sqlalchemy.orm.strategy_options import load_only, Load  # type: ignore
from service import db
from service.models import TitleRegisterData, UprnMapping, UserSearchAndResults
from datetime import datetime


def save_user_search_details(params):
    """
    Save user's search request details, for audit purposes.

    Return cart id. as a hash with "block_size" of 64.
    """
    uf = 'utf-8'
    hash = hashlib.sha1()
    hash.update(bytes(params['MC_userId'], uf))
    hash.update(bytes(params['MC_timestamp'], uf))

    # Convert byte hash to string, for DB usage (max. len 64 for DB2).
    cart_id = hash.hexdigest()[:30]

    user_search_request = UserSearchAndResults(
        search_datetime=params['MC_timestamp'],
        user_id=params['MC_userId'],
        title_number=params['MC_titleNumber'],
        search_type=params['MC_searchType'],
        purchase_type=params['MC_purchaseType'],
        amount=params['amount'],
        cart_id=cart_id,
        viewed_datetime=None,
        lro_trans_ref=None,
    )

    db.session.add(user_search_request)
    db.session.commit()

    return cart_id


def user_can_view(user_id, title_number):
    """
    Get user's view details, after payment.

    Returns True/False according to whether query gives a result or not.
    """

    # Get only those records (per user/title) for which 'viewed_datetime' is not set.
    kwargs = {"user_id": user_id, "title_number": title_number, "viewed_datetime": None}
    view = UserSearchAndResults.query.filter_by(**kwargs).first()

    # 'viewed_datetime' tracks "once-only" usage.
    if view:
        if view.viewed_datetime is None:

            # Update row.
            view.viewed_datetime = _get_time()
            db.session.commit()

    return view is not None


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


def _get_time():
    # Postgres datetime format is YYYY-MM-DD MM:HH:SS.mm
    _now = datetime.now()
    return _now.strftime("%Y-%m-%d %H:%M:%S.%f")
