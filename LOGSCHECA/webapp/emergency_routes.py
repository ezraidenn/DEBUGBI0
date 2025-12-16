"""
Rutas API para el sistema de emergencias.
"""
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from webapp.models import db, Zone, Group, GroupMember, EmergencySession, RollCallEntry
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

emergency_bp = Blueprint('emergency', __name__)


# ============================================
# PÁGINAS
# ============================================

@emergency_bp.route('/config')
@login_required
def config_page():
    """Página de configuración"""
    if not current_user.is_admin:
        return "Acceso denegado", 403
    return render_template('emergency_config.html')


@emergency_bp.route('/emergency')
@login_required
def emergency_page():
    """Página de emergencias"""
    if not current_user.is_admin:
        return "Acceso denegado", 403
    return render_template('emergency_center.html')


# ============================================
# API - ZONAS
# ============================================

@emergency_bp.route('/api/zones', methods=['GET'])
@login_required
def get_zones():
    """Obtener todas las zonas"""
    try:
        zones = Zone.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'zones': [{
                'id': z.id,
                'name': z.name,
                'description': z.description,
                'color': z.color,
                'icon': z.icon,
                'groups_count': z.groups.count()
            } for z in zones]
        })
    except Exception as e:
        logger.error(f"Error obteniendo zonas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/zones', methods=['POST'])
@login_required
def create_zone():
    """Crear nueva zona"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        data = request.json
        zone = Zone(
            name=data['name'],
            description=data.get('description', ''),
            color=data.get('color', '#6c757d'),
            icon=data.get('icon', 'bi-building')
        )
        db.session.add(zone)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'zone': {
                'id': zone.id,
                'name': zone.name,
                'description': zone.description,
                'color': zone.color,
                'icon': zone.icon
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creando zona: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/zones/<int:zone_id>', methods=['PUT'])
@login_required
def update_zone(zone_id):
    """Actualizar zona"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        zone = Zone.query.get_or_404(zone_id)
        data = request.json
        
        zone.name = data.get('name', zone.name)
        zone.description = data.get('description', zone.description)
        zone.color = data.get('color', zone.color)
        zone.icon = data.get('icon', zone.icon)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Zona actualizada'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error actualizando zona: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/zones/<int:zone_id>', methods=['DELETE'])
@login_required
def delete_zone(zone_id):
    """Eliminar zona (soft delete)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        zone = Zone.query.get_or_404(zone_id)
        zone.is_active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Zona eliminada'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error eliminando zona: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# API - GRUPOS
# ============================================

@emergency_bp.route('/api/zones/<int:zone_id>/groups', methods=['GET'])
@login_required
def get_groups(zone_id):
    """Obtener grupos de una zona"""
    try:
        groups = Group.query.filter_by(zone_id=zone_id, is_active=True).all()
        return jsonify({
            'success': True,
            'groups': [{
                'id': g.id,
                'name': g.name,
                'description': g.description,
                'color': g.color,
                'members_count': g.members.count()
            } for g in groups]
        })
    except Exception as e:
        logger.error(f"Error obteniendo grupos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/groups', methods=['POST'])
@login_required
def create_group():
    """Crear nuevo grupo"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        data = request.json
        group = Group(
            name=data['name'],
            description=data.get('description', ''),
            zone_id=data['zone_id'],
            color=data.get('color', '#007bff')
        )
        db.session.add(group)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'group': {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'color': group.color
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creando grupo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
@login_required
def delete_group(group_id):
    """Eliminar grupo"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        group = Group.query.get_or_404(group_id)
        group.is_active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Grupo eliminado'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error eliminando grupo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# API - BÚSQUEDA DE USUARIOS
# ============================================

@emergency_bp.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    """Buscar usuarios de BioStar"""
    try:
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({'success': True, 'users': []})
        
        # Importar la función de filtrado
        from src.utils.user_filter import get_filtered_users
        
        # Obtener usuarios filtrados
        all_users = get_filtered_users()
        
        # Buscar por nombre o ID
        query_lower = query.lower()
        results = []
        for user in all_users:
            user_name = user.get('name', '').lower()
            user_id = str(user.get('user_id', '')).lower()
            
            if query_lower in user_name or query_lower in user_id:
                results.append({
                    'user_id': user.get('user_id'),
                    'name': user.get('name'),
                    'user_group_id': user.get('user_group_id', {})
                })
                
                if len(results) >= 20:  # Limitar resultados
                    break
        
        return jsonify({'success': True, 'users': results})
    except Exception as e:
        logger.error(f"Error buscando usuarios: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# API - MIEMBROS DE GRUPOS
# ============================================

@emergency_bp.route('/api/groups/<int:group_id>/members', methods=['GET'])
@login_required
def get_group_members(group_id):
    """Obtener miembros de un grupo"""
    try:
        members = GroupMember.query.filter_by(group_id=group_id).all()
        return jsonify({
            'success': True,
            'members': [{
                'id': m.id,
                'biostar_user_id': m.biostar_user_id,
                'user_name': m.user_name,
                'added_at': m.added_at.isoformat() if m.added_at else None
            } for m in members]
        })
    except Exception as e:
        logger.error(f"Error obteniendo miembros: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/groups/<int:group_id>/members', methods=['POST'])
@login_required
def add_group_member(group_id):
    """Agregar usuario a grupo"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        data = request.json
        
        # Verificar si ya existe
        existing = GroupMember.query.filter_by(
            group_id=group_id,
            biostar_user_id=data['biostar_user_id']
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Usuario ya está en el grupo'}), 400
        
        member = GroupMember(
            group_id=group_id,
            biostar_user_id=data['biostar_user_id'],
            user_name=data['user_name']
        )
        db.session.add(member)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Usuario agregado al grupo'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error agregando miembro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/groups/<int:group_id>/members/<int:member_id>', methods=['DELETE'])
@login_required
def remove_group_member(group_id, member_id):
    """Remover usuario de grupo"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        member = GroupMember.query.filter_by(id=member_id, group_id=group_id).first_or_404()
        db.session.delete(member)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Usuario removido del grupo'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removiendo miembro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# API - EMERGENCIAS
# ============================================

@emergency_bp.route('/api/emergency/status', methods=['GET'])
@login_required
def get_emergency_status():
    """Obtener estado de emergencias activas"""
    try:
        active = EmergencySession.query.filter_by(status='active').all()
        return jsonify({
            'success': True,
            'has_active': len(active) > 0,
            'emergencies': [{
                'id': e.id,
                'zone_id': e.zone_id,
                'zone_name': e.zone.name,
                'emergency_type': e.emergency_type,
                'started_at': e.started_at.isoformat(),
                'started_by': e.started_by_user.username
            } for e in active]
        })
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/emergency/activate', methods=['POST'])
@login_required
def activate_emergency():
    """Activar emergencia en una zona"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        data = request.json
        zone_id = data['zone_id']
        
        # Verificar si ya hay emergencia activa en esta zona
        existing = EmergencySession.query.filter_by(
            zone_id=zone_id,
            status='active'
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Ya hay una emergencia activa en esta zona'}), 400
        
        # Crear sesión de emergencia
        emergency = EmergencySession(
            zone_id=zone_id,
            emergency_type=data.get('emergency_type', 'general'),
            started_by=current_user.id,
            notes=data.get('notes', '')
        )
        db.session.add(emergency)
        db.session.flush()  # Para obtener el ID
        
        # Crear entradas de pase de lista para todos los miembros de todos los grupos de la zona
        zone = Zone.query.get(zone_id)
        for group in zone.groups.filter_by(is_active=True):
            for member in group.members:
                entry = RollCallEntry(
                    emergency_id=emergency.id,
                    group_id=group.id,
                    biostar_user_id=member.biostar_user_id,
                    user_name=member.user_name,
                    status='pending'
                )
                db.session.add(entry)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'emergency_id': emergency.id,
            'message': 'Emergencia activada'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error activando emergencia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/emergency/<int:emergency_id>/resolve', methods=['POST'])
@login_required
def resolve_emergency(emergency_id):
    """Resolver emergencia"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        emergency = EmergencySession.query.get_or_404(emergency_id)
        emergency.status = 'resolved'
        emergency.resolved_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Emergencia resuelta'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resolviendo emergencia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# API - PASE DE LISTA
# ============================================

@emergency_bp.route('/api/emergency/<int:emergency_id>/roll-call', methods=['GET'])
@login_required
def get_roll_call(emergency_id):
    """Obtener pase de lista de una emergencia"""
    try:
        entries = RollCallEntry.query.filter_by(emergency_id=emergency_id).all()
        
        # Agrupar por grupo
        grouped = {}
        for entry in entries:
            group_name = entry.group.name
            if group_name not in grouped:
                grouped[group_name] = {
                    'group_id': entry.group_id,
                    'group_name': group_name,
                    'group_color': entry.group.color,
                    'members': []
                }
            
            grouped[group_name]['members'].append({
                'id': entry.id,
                'biostar_user_id': entry.biostar_user_id,
                'user_name': entry.user_name,
                'status': entry.status,
                'marked_at': entry.marked_at.isoformat() if entry.marked_at else None,
                'marked_by': entry.marked_by_user.username if entry.marked_by else None,
                'notes': entry.notes
            })
        
        return jsonify({
            'success': True,
            'groups': list(grouped.values())
        })
    except Exception as e:
        logger.error(f"Error obteniendo pase de lista: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/roll-call/<int:entry_id>/mark', methods=['POST'])
@login_required
def mark_attendance(entry_id):
    """Marcar asistencia en pase de lista"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        data = request.json
        entry = RollCallEntry.query.get_or_404(entry_id)
        
        entry.status = data['status']  # present, absent
        entry.marked_by = current_user.id
        entry.marked_at = datetime.utcnow()
        entry.notes = data.get('notes', '')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Asistencia marcada'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marcando asistencia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
