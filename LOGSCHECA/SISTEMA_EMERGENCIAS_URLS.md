# 🚨 Sistema de Emergencias - URLs de Acceso

## 📍 **URLs Directas:**

### **Página de Configuración**
```
http://localhost:5000/config
```
**Funciones:**
- Ver y crear zonas (Casa Club, Gimnasio, etc.)
- Ver y crear grupos (IT, Desarrollo, Diseño)
- Buscar usuarios de BioStar
- Asignar usuarios a grupos
- Remover usuarios de grupos

---

### **Centro de Emergencias**
```
http://localhost:5000/emergency
```
**Funciones:**
- Seleccionar zona
- Activar emergencia con botón grande rojo
- Pase de lista en tiempo real agrupado por departamentos
- Marcar presente/ausente
- Ver estadísticas en vivo
- Resolver emergencia

---

## 🔧 **APIs Disponibles:**

### **Zonas**
- `GET /api/zones` - Listar zonas
- `POST /api/zones` - Crear zona
- `PUT /api/zones/<id>` - Actualizar zona
- `DELETE /api/zones/<id>` - Eliminar zona

### **Grupos**
- `GET /api/zones/<zone_id>/groups` - Listar grupos de una zona
- `POST /api/groups` - Crear grupo
- `DELETE /api/groups/<id>` - Eliminar grupo

### **Miembros**
- `GET /api/groups/<group_id>/members` - Listar miembros
- `POST /api/groups/<group_id>/members` - Agregar miembro
- `DELETE /api/groups/<group_id>/members/<member_id>` - Remover miembro

### **Emergencias**
- `GET /api/emergency/status` - Estado de emergencias activas
- `POST /api/emergency/activate` - Activar emergencia
- `POST /api/emergency/<id>/resolve` - Resolver emergencia

### **Pase de Lista**
- `GET /api/emergency/<emergency_id>/roll-call` - Obtener pase de lista
- `POST /api/roll-call/<entry_id>/mark` - Marcar asistencia

---

## 🎯 **Flujo de Uso:**

### **1. Configuración Inicial** (Una sola vez)
1. Ve a http://localhost:5000/config
2. Verás "Casa Club" ya creada con 3 grupos (IT, Desarrollo, Diseño)
3. Click en "Casa Club" para ver los grupos
4. Click en "Ver" en cada grupo
5. Busca usuarios y agrégalos

### **2. Uso en Emergencia**
1. Ve a http://localhost:5000/emergency
2. Click en la tarjeta "Casa Club"
3. Click en el botón rojo **"ACTIVAR EMERGENCIA"**
4. Selecciona tipo de emergencia
5. Aparece el pase de lista agrupado:
   ```
   IT
   - Usuario 1 [Presente] [Ausente]
   - Usuario 2 [Presente] [Ausente]
   
   Desarrollo
   - Usuario 3 [Presente] [Ausente]
   ```
6. Marca asistencias en tiempo real
7. Click en "Resolver Emergencia" cuando termine

---

## ✅ **Estado Actual:**

```
✅ Tablas creadas
✅ Zona "Casa Club" creada
✅ 3 grupos creados (IT, Desarrollo, Diseño)
✅ API funcionando
✅ Páginas HTML funcionando
✅ Servidor corriendo en puerto 5000
```

---

## 🔗 **Acceso Rápido:**

**Copia y pega en tu navegador:**

- Configuración: http://localhost:5000/config
- Emergencias: http://localhost:5000/emergency

**¡El sistema está funcionando!** 🚀
