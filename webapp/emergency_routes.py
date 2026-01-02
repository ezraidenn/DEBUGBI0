"""
Rutas API para el sistema de emergencias con soporte de tiempo real.
"""
from flask import Blueprint, jsonify, request, render_template, Response, stream_with_context
from flask_login import login_required, current_user
from webapp.models import db, Zone, Group, GroupMember, EmergencySession, RollCallEntry, ZoneDevice
from datetime import datetime
import logging
import json
import time

logger = logging.getLogger(__name__)

emergency_bp = Blueprint('emergency', __name__, url_prefix='/emergency')


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
        logger.info(f"📍 Obteniendo zonas: {len(zones)} encontradas")
        
        result = {
            'success': True,
            'zones': [{
                'id': z.id,
                'name': z.name,
                'description': z.description,
                'color': z.color,
                'icon': z.icon,
                'groups_count': z.groups.count()
            } for z in zones]
        }
        
        logger.info(f"Zonas devueltas: {[z['name'] for z in result['zones']]}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error obteniendo zonas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/zones', methods=['POST'])
@login_required
def create_zone():
    """Crear nueva zona"""
    if not current_user.is_admin:
        logger.warning(f"Usuario {current_user.username} intentó crear zona sin permisos")
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        data = request.json
        logger.info(f"Creando zona: {data}")
        
        zone = Zone(
            name=data['name'],
            description=data.get('description', ''),
            color=data.get('color', '#6c757d'),
            icon=data.get('icon', 'bi-building')
        )
        db.session.add(zone)
        db.session.commit()
        
        logger.info(f"✅ Zona creada exitosamente: ID={zone.id}, Nombre={zone.name}")
        
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
        logger.error(f"❌ Error creando zona: {e}")
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
# API - BÚSQUEDA DE USUARIOS (directo desde BioStar)
# ============================================

@emergency_bp.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    """
    Buscar usuarios directamente desde la API de BioStar.
    Más rápido que iterar sobre eventos.
    """
    try:
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({'success': True, 'users': []})
        
        # Importar monitor
        from webapp.app import get_monitor
        monitor = get_monitor()
        
        if not monitor or not monitor.client:
            return jsonify({'success': False, 'message': 'Error conectando a BioStar'}), 500
        
        # Buscar usuarios directamente en BioStar
        biostar_users = monitor.client.search_users(query, limit=50)
        
        # Formatear resultados
        results = []
        for user in biostar_users:
            user_id = user.get('user_id') or user.get('id')
            user_name = user.get('name', '')
            
            if user_id:
                results.append({
                    'user_id': str(user_id),
                    'name': user_name or f'Usuario {user_id}'
                })
        
        logger.info(f"Búsqueda BioStar '{query}': {len(results)} usuarios encontrados")
        
        return jsonify({'success': True, 'users': results})
        
    except Exception as e:
        logger.error(f"Error buscando usuarios: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/users/all', methods=['GET'])
@login_required
def get_all_biostar_users():
    """
    Obtener todos los usuarios de BioStar (para precargar en el buscador).
    """
    try:
        from webapp.app import get_monitor
        monitor = get_monitor()
        
        if not monitor or not monitor.client:
            return jsonify({'success': False, 'message': 'Error conectando a BioStar'}), 500
        
        # Obtener todos los usuarios de BioStar
        biostar_users = monitor.client.get_all_users(limit=2000)
        
        # Formatear resultados
        results = []
        for user in biostar_users:
            user_id = user.get('user_id') or user.get('id')
            user_name = user.get('name', '')
            
            if user_id:
                results.append({
                    'user_id': str(user_id),
                    'name': user_name or f'Usuario {user_id}'
                })
        
        # Ordenar por nombre
        results.sort(key=lambda x: x.get('name', '').lower())
        
        logger.info(f"Usuarios BioStar cargados: {len(results)}")
        
        return jsonify({
            'success': True, 
            'users': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {e}")
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
    """Activar emergencia en una zona - Desbloquea puertas y activa alarmas"""
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
        
        # ========== ACTIVAR DISPOSITIVOS DE LA ZONA ==========
        # Obtener opciones del request
        unlock_doors = data.get('unlock_doors', True)
        trigger_alarms = data.get('trigger_alarms', False)
        
        # Obtener dispositivos asignados a esta zona
        zone_devices = ZoneDevice.query.filter_by(zone_id=zone_id, is_active=True).all()
        devices_activated = []
        devices_failed = []
        unlocked_door_ids = []  # Para guardar y poder cerrar después
        
        logger.info(f"🚨 Emergencia activada en zona {zone_id} - Desbloquear: {unlock_doors}, Alarmas: {trigger_alarms}")
        logger.info(f"   Dispositivos en zona: {len(zone_devices)}")
        
        if zone_devices and (unlock_doors or trigger_alarms):
            # Importar el monitor de BioStar
            from webapp.app import get_monitor
            monitor = get_monitor()
            
            if monitor and monitor.client:
                for zd in zone_devices:
                    device_id = zd.device_id
                    device_name = zd.device_name or f"Dispositivo {device_id}"
                    
                    try:
                        unlocked = False
                        door_id = None
                        alarm_triggered = False
                        
                        # Desbloquear puerta PERMANENTEMENTE si está habilitado
                        if unlock_doors:
                            logger.info(f"   🔓 Desbloqueando puerta del dispositivo {device_id} (permanente)...")
                            # Usar unlock_door_by_device para mantener abierta hasta resolver
                            unlocked, door_id = monitor.client.unlock_door_by_device(device_id)
                            if door_id:
                                unlocked_door_ids.append(door_id)
                        
                        # Activar alarma si está habilitado
                        if trigger_alarms:
                            logger.info(f"   🔔 Activando alarma del dispositivo {device_id}...")
                            alarm_triggered = monitor.client.trigger_alarm(device_id)
                        
                        if unlocked or alarm_triggered:
                            devices_activated.append({
                                'device_id': device_id,
                                'door_id': door_id,
                                'name': device_name,
                                'unlocked': unlocked,
                                'alarm': alarm_triggered
                            })
                            logger.info(f"   ✓ Dispositivo {device_name} - Puerta {door_id}: {unlocked}, Alarma: {alarm_triggered}")
                        else:
                            devices_failed.append({
                                'device_id': device_id,
                                'name': device_name,
                                'error': 'No se pudo activar (puede que el dispositivo no soporte estas funciones)'
                            })
                            logger.warning(f"   ⚠ Dispositivo {device_name} no respondió")
                    except Exception as dev_error:
                        logger.error(f"   ✗ Error en dispositivo {device_name}: {dev_error}")
                        devices_failed.append({
                            'device_id': device_id,
                            'name': device_name,
                            'error': str(dev_error)
                        })
                
                # Guardar las puertas desbloqueadas en la emergencia
                if unlocked_door_ids:
                    import json
                    emergency.unlocked_doors = json.dumps(unlocked_door_ids)
                    db.session.commit()
                    logger.info(f"   📝 Puertas guardadas para cerrar al resolver: {unlocked_door_ids}")
            else:
                logger.warning("⚠ Monitor de BioStar no disponible para activar dispositivos")
        elif not zone_devices:
            logger.info("   ℹ No hay dispositivos asignados a esta zona")
        
        return jsonify({
            'success': True,
            'emergency_id': emergency.id,
            'message': 'Emergencia activada',
            'devices': {
                'total': len(zone_devices),
                'activated': devices_activated,
                'failed': devices_failed
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error activando emergencia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/emergency/<int:emergency_id>/resolve', methods=['POST'])
@login_required
def resolve_emergency(emergency_id):
    """Resolver emergencia - cierra las puertas que fueron desbloqueadas"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        emergency = EmergencySession.query.get_or_404(emergency_id)
        
        # ========== CERRAR PUERTAS DESBLOQUEADAS ==========
        doors_released = []
        doors_failed = []
        
        if emergency.unlocked_doors:
            import json
            try:
                door_ids = json.loads(emergency.unlocked_doors)
                logger.info(f"🔒 Cerrando puertas de emergencia {emergency_id}: {door_ids}")
                
                from webapp.app import get_monitor
                monitor = get_monitor()
                
                if monitor and monitor.client:
                    for door_id in door_ids:
                        try:
                            success = monitor.client.release_door(door_id)
                            if success:
                                doors_released.append(door_id)
                                logger.info(f"   ✓ Puerta {door_id} liberada (vuelve a modo normal)")
                            else:
                                doors_failed.append(door_id)
                                logger.warning(f"   ⚠ No se pudo liberar puerta {door_id}")
                        except Exception as door_error:
                            logger.error(f"   ✗ Error liberando puerta {door_id}: {door_error}")
                            doors_failed.append(door_id)
                else:
                    logger.warning("⚠ Monitor de BioStar no disponible para cerrar puertas")
            except json.JSONDecodeError:
                logger.error(f"Error parseando unlocked_doors: {emergency.unlocked_doors}")
        
        # Marcar emergencia como resuelta
        emergency.status = 'resolved'
        emergency.resolved_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Emergencia resuelta',
            'doors': {
                'released': doors_released,
                'failed': doors_failed,
                'total': len(doors_released) + len(doors_failed)
            }
        })
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


# ============================================
# SSE - TIEMPO REAL PARA EMERGENCIAS
# ============================================

@emergency_bp.route('/stream/emergency/<int:emergency_id>')
@login_required
def stream_emergency(emergency_id):
    """
    Stream SSE para actualizaciones en tiempo real de una emergencia.
    Detecta cambios en el pase de lista y eventos de BioStar.
    """
    def generate():
        last_check = datetime.utcnow()
        poll_count = 0
        
        # Enviar mensaje de conexión
        yield f"event: connection\ndata: {json.dumps({'type': 'connected', 'emergency_id': emergency_id})}\n\n"
        
        while True:
            try:
                poll_count += 1
                
                # Verificar si la emergencia sigue activa
                emergency = EmergencySession.query.get(emergency_id)
                if not emergency or emergency.status != 'active':
                    yield f"event: emergency_resolved\ndata: {json.dumps({'message': 'Emergencia resuelta'})}\n\n"
                    break
                
                # Obtener estado actual del pase de lista
                entries = RollCallEntry.query.filter_by(emergency_id=emergency_id).all()
                
                stats = {
                    'total': len(entries),
                    'present': sum(1 for e in entries if e.status == 'present'),
                    'absent': sum(1 for e in entries if e.status == 'absent'),
                    'pending': sum(1 for e in entries if e.status == 'pending')
                }
                
                # Buscar cambios recientes (marcados después de last_check)
                recent_changes = []
                for entry in entries:
                    if entry.marked_at and entry.marked_at > last_check:
                        recent_changes.append({
                            'id': entry.id,
                            'user_name': entry.user_name,
                            'biostar_user_id': entry.biostar_user_id,
                            'status': entry.status,
                            'marked_at': entry.marked_at.isoformat(),
                            'marked_by': entry.marked_by_user.username if entry.marked_by else 'Sistema',
                            'group_id': entry.group_id
                        })
                
                # Auto-detectar presencia basada en eventos de BioStar
                auto_marked = auto_mark_presence_from_biostar(emergency_id, entries)
                
                # Enviar actualización
                update_data = {
                    'stats': stats,
                    'recent_changes': recent_changes,
                    'auto_marked': auto_marked,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                yield f"event: update\ndata: {json.dumps(update_data)}\n\n"
                
                # Actualizar timestamp
                last_check = datetime.utcnow()
                
                # Heartbeat cada 8 polls (16 segundos)
                if poll_count % 8 == 0:
                    yield f"event: heartbeat\ndata: {json.dumps({'status': 'alive'})}\n\n"
                
                time.sleep(2)  # Poll cada 2 segundos
                
            except Exception as e:
                logger.error(f"Error en stream de emergencia: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                time.sleep(5)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


# ============================================
# API - DISPOSITIVOS POR ZONA (para control de emergencias: sonido/desbloqueo)
# ============================================

@emergency_bp.route('/api/zones/<int:zone_id>/devices', methods=['GET'])
@login_required
def get_zone_devices(zone_id):
    """Obtener dispositivos asignados a una zona para control de emergencias"""
    try:
        devices = ZoneDevice.query.filter_by(zone_id=zone_id, is_active=True).all()
        return jsonify({
            'success': True,
            'devices': [{
                'id': d.id,
                'device_id': d.device_id,
                'device_name': d.device_name,
                'device_type': d.device_type if hasattr(d, 'device_type') else 'checador',
                'added_at': d.added_at.isoformat() if d.added_at else None
            } for d in devices]
        })
    except Exception as e:
        logger.error(f"Error obteniendo dispositivos de zona: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/zones/<int:zone_id>/devices', methods=['POST'])
@login_required
def add_zone_device(zone_id):
    """Agregar dispositivo a una zona para control de emergencias"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        data = request.json
        
        # Verificar si ya existe
        existing = ZoneDevice.query.filter_by(
            zone_id=zone_id,
            device_id=data['device_id']
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Dispositivo ya está asignado a esta zona'}), 400
        
        device = ZoneDevice(
            zone_id=zone_id,
            device_id=data['device_id'],
            device_name=data.get('device_name', f"Dispositivo {data['device_id']}"),
        )
        db.session.add(device)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Dispositivo agregado a la zona'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error agregando dispositivo a zona: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/zones/<int:zone_id>/devices/<int:device_id>', methods=['DELETE'])
@login_required
def remove_zone_device(zone_id, device_id):
    """Remover dispositivo de una zona"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permiso denegado'}), 403
    
    try:
        device = ZoneDevice.query.filter_by(zone_id=zone_id, device_id=device_id).first_or_404()
        db.session.delete(device)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Dispositivo removido de la zona'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removiendo dispositivo de zona: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@emergency_bp.route('/api/devices/available', methods=['GET'])
@login_required
def get_available_devices():
    """Obtener lista de dispositivos disponibles de BioStar"""
    try:
        from src.api.device_monitor import DeviceMonitor
        from src.utils.config import Config
        
        config = Config()
        monitor = DeviceMonitor(config)
        
        if not monitor.login():
            return jsonify({'success': False, 'message': 'Error conectando a BioStar'}), 500
        
        devices = monitor.get_all_devices(refresh=True)
        
        return jsonify({
            'success': True,
            'devices': [{
                'id': d.get('id'),
                'name': d.get('name', f"Dispositivo {d.get('id')}")
            } for d in devices]
        })
    except Exception as e:
        logger.error(f"Error obteniendo dispositivos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# SSE - CHECKLIST EN TIEMPO REAL MULTI-DISPOSITIVO
# ============================================

@emergency_bp.route('/stream/zone/<int:zone_id>/presence')
@login_required
def stream_zone_presence(zone_id):
    """
    Stream SSE para presencia en tiempo real de una zona.
    Detecta eventos de BioStar en los dispositivos asignados a la zona.
    """
    def generate():
        last_check = datetime.utcnow()
        poll_count = 0
        
        # Obtener dispositivos de la zona
        zone_devices = ZoneDevice.query.filter_by(zone_id=zone_id, is_active=True).all()
        device_ids = [d.device_id for d in zone_devices]
        
        yield f"event: connection\ndata: {json.dumps({'type': 'connected', 'zone_id': zone_id, 'devices': device_ids})}\n\n"
        
        if not device_ids:
            yield f"event: error\ndata: {json.dumps({'error': 'No hay dispositivos asignados a esta zona'})}\n\n"
            return
        
        # Obtener miembros de todos los grupos de la zona
        zone = Zone.query.get(zone_id)
        all_members = {}
        for group in zone.groups.filter_by(is_active=True):
            for member in group.members:
                all_members[str(member.biostar_user_id)] = {
                    'name': member.user_name,
                    'group_id': group.id,
                    'group_name': group.name,
                    'last_seen': None,
                    'device': None
                }
        
        yield f"event: members\ndata: {json.dumps({'members': list(all_members.values()), 'total': len(all_members)})}\n\n"
        
        while True:
            try:
                poll_count += 1
                
                # Buscar eventos recientes en los dispositivos de la zona
                presence_updates = check_zone_presence(device_ids, all_members, last_check)
                
                if presence_updates:
                    yield f"event: presence\ndata: {json.dumps({'updates': presence_updates, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                
                # Heartbeat cada 8 polls
                if poll_count % 8 == 0:
                    yield f"event: heartbeat\ndata: {json.dumps({'status': 'alive'})}\n\n"
                
                last_check = datetime.utcnow()
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error en stream de presencia: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                time.sleep(5)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


def check_zone_presence(device_ids, members_map, last_check):
    """
    Verifica presencia de miembros en los dispositivos de la zona.
    Retorna lista de actualizaciones de presencia.
    """
    updates = []
    
    try:
        from src.api.device_monitor import DeviceMonitor, EVENT_CODES
        from src.utils.config import Config
        from datetime import timedelta
        
        config = Config()
        monitor = DeviceMonitor(config)
        
        if not monitor.login():
            return updates
        
        now = datetime.now()
        start_time = now - timedelta(minutes=5)
        
        for device_id in device_ids:
            try:
                events = monitor.get_device_events(device_id, start_time, now, limit=50)
                
                for event in events:
                    # Solo procesar accesos concedidos
                    event_code = event.get('event_type_id', {}).get('code', '')
                    if event_code not in EVENT_CODES.get('ACCESS_GRANTED', []):
                        continue
                    
                    # Extraer user_id
                    user_data = event.get('user_id', {})
                    if isinstance(user_data, dict):
                        user_id = str(user_data.get('user_id') or user_data.get('id', ''))
                        user_name = user_data.get('name', 'Desconocido')
                    else:
                        user_id = str(user_data) if user_data else ''
                        user_name = 'Desconocido'
                    
                    # Verificar si es miembro de la zona
                    if user_id in members_map:
                        event_time = event.get('datetime')
                        device_name = event.get('device_id', {}).get('name', f'Dispositivo {device_id}')
                        
                        # Actualizar info del miembro
                        members_map[user_id]['last_seen'] = str(event_time)
                        members_map[user_id]['device'] = device_name
                        
                        updates.append({
                            'user_id': user_id,
                            'user_name': members_map[user_id]['name'],
                            'group_name': members_map[user_id]['group_name'],
                            'device': device_name,
                            'time': str(event_time),
                            'type': 'present'
                        })
                        
            except Exception as e:
                logger.error(f"Error procesando dispositivo {device_id}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error en check_zone_presence: {e}")
    
    return updates


def auto_mark_presence_from_biostar(emergency_id, entries):
    """
    Auto-marca usuarios como presentes si tienen eventos recientes en BioStar.
    Retorna lista de usuarios auto-marcados.
    """
    auto_marked = []
    
    try:
        # Importar monitor de dispositivos
        from src.api.device_monitor import DeviceMonitor, EVENT_CODES
        from src.utils.config import Config
        
        config = Config()
        monitor = DeviceMonitor(config)
        
        if not monitor.login():
            return auto_marked
        
        # Obtener todos los dispositivos
        devices = monitor.get_all_devices(refresh=False)
        
        # Obtener IDs de usuarios pendientes
        pending_entries = {str(e.biostar_user_id): e for e in entries if e.status == 'pending'}
        
        if not pending_entries:
            return auto_marked
        
        # Buscar eventos recientes (últimos 30 minutos)
        from datetime import timedelta
        now = datetime.now()
        start_time = now - timedelta(minutes=30)
        
        for device in devices[:5]:  # Limitar a 5 dispositivos para no sobrecargar
            try:
                events = monitor.get_device_events(device['id'], start_time, now, limit=100)
                
                for event in events:
                    # Solo procesar accesos concedidos
                    event_code = event.get('event_type_id', {}).get('code', '')
                    if event_code not in EVENT_CODES['ACCESS_GRANTED']:
                        continue
                    
                    # Extraer user_id del evento
                    user_data = event.get('user_id', {})
                    if isinstance(user_data, dict):
                        user_id = str(user_data.get('user_id') or user_data.get('id', ''))
                    else:
                        user_id = str(user_data) if user_data else ''
                    
                    # Verificar si este usuario está pendiente
                    if user_id in pending_entries:
                        entry = pending_entries[user_id]
                        
                        # Auto-marcar como presente
                        entry.status = 'present'
                        entry.marked_at = datetime.utcnow()
                        entry.notes = f"Auto-detectado en {device.get('name', 'dispositivo')} a las {event.get('datetime', 'N/A')}"
                        
                        db.session.commit()
                        
                        auto_marked.append({
                            'user_name': entry.user_name,
                            'biostar_user_id': user_id,
                            'device': device.get('name', 'Desconocido'),
                            'time': str(event.get('datetime', ''))
                        })
                        
                        # Remover de pendientes
                        del pending_entries[user_id]
                        
                        logger.info(f"✅ Auto-marcado: {entry.user_name} detectado en {device.get('name')}")
                        
            except Exception as e:
                logger.error(f"Error procesando dispositivo {device.get('id')}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error en auto-marcado: {e}")
    
    return auto_marked
