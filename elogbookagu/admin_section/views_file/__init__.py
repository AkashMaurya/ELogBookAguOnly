# admin_section/views_file/__init__.py
from .add_activity_views import (
    add_activity_type,
    edit_activity_type,
    delete_activity_type,
)
from .CoreDiaProSession_views import (
    core_dia_pro_session_list,
    core_dia_pro_session_create,
    core_dia_pro_session_update,
    core_dia_pro_session_delete,
)

from .resources import CoreDiaProSessionResource
