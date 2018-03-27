"""
Copyright ©2018. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""


from boac import db, std_commit
from boac.lib.berkeley import term_name_for_sis_id
from boac.lib.util import get_args_dict
from boac.models.base import Base
from decorator import decorator
from flask import current_app as app
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified


class JsonCache(Base):
    __tablename__ = 'json_cache'

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    key = db.Column(db.String, nullable=False, unique=True)
    json = db.Column(JSONB)

    def __init__(self, key, json=None):
        self.key = key
        self.json = json

    def __repr__(self):
        return '<JsonCache {}, json={}, updated={}, created={}>'.format(
            self.key,
            self.json,
            self.updated_at,
            self.created_at,
        )


def clear(key_like):
    matches = db.session.query(JsonCache).filter(JsonCache.key.like(key_like))
    app.logger.info('Will delete {count} entries matching {key_like}'.format(count=matches.count(), key_like=key_like))
    matches.delete(synchronize_session=False)


def clear_other(key_like):
    matches = db.session.query(JsonCache).filter(JsonCache.key.notlike(key_like))
    app.logger.info('Will delete {count} entries not matching {key_like}'.format(count=matches.count(), key_like=key_like))
    matches.delete(synchronize_session=False)


def stow(key_pattern, for_term=False):
    """Use Decorator module to preserve the wrapped function's signature, allowing easy wrapping by other decorators.

    If the for_term option is enabled, the wrapped function is expected to take a term_id argument.
    TODO Mockingbird does not currently preserve signatures, and so JsonCache cannot directly wrap a @fixture.
    """
    @decorator
    def _stow(func, *args, **kw):
        args_dict = get_args_dict(func, *args, **kw)
        key = key_pattern.format(**args_dict)
        if for_term:
            term_name = term_name_for_sis_id(args_dict.get('term_id'))
            key = 'term_{}-{}'.format(
                term_name,
                key,
            )
        stowed = JsonCache.query.filter_by(key=key).first()
        # Note that the query returns a DB row rather than the value of the JSON column.
        if stowed is not None:
            app.logger.debug('Returning stowed JSON for key {key}'.format(key=key))
            return stowed.json
        else:
            app.logger.info('{key} not found in DB'.format(key=key))
            to_stow = func(*args, **kw)
            if to_stow is not None:
                app.logger.debug('Will stow JSON for key {key}'.format(key=key))
                row = JsonCache(key=key, json=to_stow)
                try:
                    db.session.add(row)
                    std_commit()
                except IntegrityError:
                    app.logger.warn('Conflict for key {key}; will attempt to return stowed JSON'.format(key=key))
                    stowed = JsonCache.query.filter_by(key=key).first()
                    if stowed is not None:
                        return stowed.json
            else:
                app.logger.info('{key} not generated and will not be stowed in DB'.format(key=key))
            return to_stow
    return _stow


def update_jsonb_row(stowed):
    """Jump through some hoops to commit changes to a JSONB column."""
    flag_modified(stowed, 'json')
    db.session.merge(stowed)
    std_commit()
