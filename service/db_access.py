import hashlib
import config
import logging
from sqlalchemy import false                                 # type: ignore
from sqlalchemy.orm.strategy_options import Load             # type: ignore
from service import db, legacy_transmission_queue
from service.models import TitleRegisterData, UprnMapping, UserSearchAndResults, Validation
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def save_user_search_details(params):
    """
    Save user's search request details, for audit purposes.

    Return cart id. as a hash with "block_size" of 64.
    :param params:
    """
    logger.debug('Start save_user_search_details')
    logger.debug(params)
    uf = 'utf-8'
    hash = hashlib.sha1()
    hash.update(bytes(params['MC_titleNumber'], uf))
    hash.update(bytes(params['last_changed_datestring'], uf))
    hash.update(bytes(params['last_changed_timestring'], uf))

    # Convert byte hash to string, for DB usage
    # Max. length of corresponding LRO_SESSION_ID is 64 for DB2 but we don't care much about that at present ;-)
    cart_id = hash.hexdigest()[:30]

    user_search_request = UserSearchAndResults(
        search_datetime=params['MC_timestamp'],
        user_id=params['MC_userId'],
        title_number=params['MC_titleNumber'],
        search_type=params['MC_searchType'],
        purchase_type=params['MC_purchaseType'],
        # needs to be in pence
        amount=int(float(params['amount']) * 100),
        cart_id=cart_id,
        viewed_datetime=None,
        lro_trans_ref=None,
        valid=False,
    )
    logger.info('Sending to PostGres')
    # Insert to DB.
    db.session.add(user_search_request)
    db.session.commit()
    logger.info('Finished sending to PostGres')

    # Put message on queue.
    prepped_message = _create_queue_message(params, cart_id)
    logger.info('Sending to legacy transmission queue')
    logger.debug(prepped_message)
    legacy_transmission_queue.send_legacy_transmission(prepped_message)
    logger.info('Finished sending to transmission queue')
    logger.debug('End save_user_search_details - returning cartId: {}'.format(cart_id))
    return cart_id

# TODO: Check that this code is valid. What happens if a user pays for the same title again, for example?
def user_can_view(user_id, title_number):
    """
    Get user's view details, after payment.

    Returns True/False according to whether "viewing window" is valid or not.
    :param user_id:
    :param title_number:
    """
    logger.debug('Start user_can_view')
    status = False

    # Get relevant record (only one assumed).
    kwargs = {"user_id": user_id, "title_number": title_number}
    logger.info('retreiving date and time of viewing')
    view = UserSearchAndResults.query.filter_by(**kwargs).order_by(UserSearchAndResults.viewed_datetime.desc().nullslast()).first()

    # 'viewed_datetime' denotes initial "access time" usage; name reflects different, earlier usage.
    if view and view.viewed_datetime and view.valid:

        minutes = int(config.CONFIG_DICT['VIEW_WINDOW_TIME'])
        viewing_duration = datetime.now() - view.viewed_datetime
        view_window_time = timedelta(minutes=minutes)

        status = viewing_duration < view_window_time
    logger.debug('End user_can_view. Returning {}'.format(status))
    return status


def get_price(product):
    result = Validation.query.filter_by(product=product).first()
    return result.price


def get_title_register(title_number):
    if title_number:
        logger.debug('Start get_title_register using {}'.format(title_number))
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
        logger.debug('Returning result: {}'.format(result))
        logger.debug('End get_title_register')
        return result
    else:
        logger.debug('End get_title_register - No title number received')
        raise TypeError('Title number must not be None.')


def get_title_registers(title_numbers):
    logger.debug('Start get_title_registers using {}'.format(title_numbers))
    # Will retrieve matching titles that are not marked as deleted
    fields = [TitleRegisterData.title_number.name, TitleRegisterData.register_data.name,
              TitleRegisterData.geometry_data.name]
    query = TitleRegisterData.query.options(Load(TitleRegisterData).load_only(*fields))
    results = query.filter(TitleRegisterData.title_number.in_(title_numbers),
                           TitleRegisterData.is_deleted == false()).all()
    logger.debug('Returning results: {}'.format(results))
    logger.debug('End get_title_registers ')
    return results


def get_official_copy_data(title_number):
    logger.debug('Start get_official_copy_data using: {}'.format(title_number))
    result = TitleRegisterData.query.options(
        Load(TitleRegisterData).load_only(
            TitleRegisterData.title_number.name,
            TitleRegisterData.official_copy_data.name
        )
    ).filter(
        TitleRegisterData.title_number == title_number,
        TitleRegisterData.is_deleted == false()
    ).first()
    logger.debug('Returning result: {}'.format(result))
    logger.debug('End get_official_copy_data')
    return result


def get_title_number_and_register_data(lr_uprn):
    logger.debug('Start get_title_number_and_register_data using: {}'.format(lr_uprn))
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
    logger.debug('Returning result: {}'.format(result))
    logger.debug('End get_title_number_and_register_data')
    if result:
        return result[0]
    else:
        return None


def get_mapped_lruprn(address_base_uprn):
    logger.debug('Start get_mapped_lruprn using {}'.format(address_base_uprn))
    result = UprnMapping.query.options(
        Load(UprnMapping).load_only(
            UprnMapping.lr_uprn.name,
            UprnMapping.uprn.name
        )
    ).filter(
        UprnMapping.uprn == address_base_uprn
    ).first()
    logger.debug('Returning result: {}'.format(result))
    logger.debug('End get_mapped_lruprn')
    return result


def _get_time():
    # Postgres datetime format is YYYY-MM-DD MM:HH:SS.mm
    _now = datetime.now()
    return _now.strftime("%Y-%m-%d %H:%M:%S.%f")


def _create_queue_message(params, cart_id):
    """
    Using parameters fed into the original method we need to create a json version with different keys
    :param params:
    :param cart_id:
    :return:
    """
    return {'search_datetime': params['MC_timestamp'],
            'user_id': params['MC_userId'],
            'title_number': params['MC_titleNumber'],
            'search_type': params['MC_searchType'],
            'purchase_type': params['MC_purchaseType'],
            # needs to be in pence
            'amount': int(float(params['amount']) * 100),
            'cart_id': cart_id,
            'viewed_datetime': None,
            'lro_trans_ref': None}
