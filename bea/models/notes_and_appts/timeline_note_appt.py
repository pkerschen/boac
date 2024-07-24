"""
Copyright ©2024. The Regents of the University of California (Regents). All Rights Reserved.

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

from bea.models.notes_and_appts.timeline_record import TimelineRecord
from bea.test_utils import utils


class TimelineNoteAppt(TimelineRecord):

    @property
    def advisor(self):
        return self.data['advisor']

    @advisor.setter
    def advisor(self, value):
        self.data['advisor'] = value

    @property
    def attachments(self):
        try:
            return self.data['attachments']
        except KeyError:
            return []

    @attachments.setter
    def attachments(self, value):
        self.data['attachments'] = value

    @property
    def topics(self):
        try:
            return self.data['topics']
        except KeyError:
            return []

    @topics.setter
    def topics(self, value):
        self.data['topics'] = value

    @property
    def contact_type(self):
        return utils.safe_key(self.data, 'contact_type')

    @contact_type.setter
    def contact_type(self, value):
        self.data['contact_type'] = value
