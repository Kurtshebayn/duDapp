# Riesgos y Mitigaciones — v1

## R-01 — Cold starts en Render (tier gratuito)

**Riesgo:** El backend en Render se suspende tras ~15 minutos de inactividad. La primera request después de eso puede tardar 30-60 segundos. Esto afecta directamente al admin que necesita registrar resultados rápido, y al espectador que abre el link por primera vez.

**Probabilidad:** Alta (ocurrirá cada vez que no haya tráfico reciente).

**Impacto:** Medio. Experiencia degradada pero funcional — el sistema responde, solo tarda más la primera vez.

**Mitigación:** Aceptar la limitación para el MVP como trade-off del tier gratuito. Mostrar un indicador de carga en el frontend para que el usuario sepa que el sistema está respondiendo. Si en el futuro la experiencia es inaceptable, migrar al tier pago de Render que mantiene el servicio activo.

## R-02 — CORS mal configurado

**Riesgo:** El frontend (Vercel) y el backend (Render) están en dominios distintos. Si CORS no se configura correctamente desde el inicio, las requests del frontend al backend fallan silenciosamente. Este es un error común y difícil de debuggear para alguien sin experiencia previa.

**Probabilidad:** Media.

**Impacto:** Alto. La aplicación simplemente no funciona hasta que se resuelve.

**Mitigación:** Configurar CORS como una de las primeras tareas del backend, antes de implementar cualquier lógica de negocio. Documentar la configuración exacta en el proyecto. Validar con una request de prueba simple antes de avanzar.

## R-03 — Backup periódico de la base de datos (Neon)

**Riesgo:** Neon (tier gratuito) no tiene auto-delete por inactividad, pero no incluye backups automáticos exportables a destinos externos (solo PITR de 24 horas). Ante un incidente grave de la cuenta, error humano o caída del proveedor, los datos podrían perderse sin un backup externo reciente.

**Probabilidad:** Baja.

**Impacto:** Crítico. Perder una temporada entera de datos no tiene vuelta atrás.

**Estado:** Mitigado. Script `backend/scripts/backup_db.py` implementado (pg_dump → archivo local). Ejecutar manualmente al menos una vez por semana durante temporada activa. Cleanup de datos sensibles completado el 2026-05-01.

## R-04 — Drag & drop deficiente en móvil

**Riesgo:** El drag & drop es la interacción central del admin (CU-02 y CU-03) y se usará principalmente desde el celular. Las implementaciones de drag & drop en pantallas táctiles pequeñas pueden ser imprecisas, lentas o frustrantes. Si esta experiencia falla, el producto entero falla para el admin.

**Probabilidad:** Media.

**Impacto:** Crítico. El admin necesita registrar resultados en menos de 2 minutos; un drag & drop torpe lo impide.

**Mitigación:** Elegir una librería con soporte sólido para touch (dnd-kit tiene buen soporte móvil). Probar la interacción en dispositivos reales desde las primeras iteraciones del frontend. Tener como plan B una interfaz alternativa de selección (dropdowns o taps) si el drag & drop en móvil resulta inviable.

## R-05 — Único punto de falla del admin

**Riesgo:** Solo existe un admin con JWT propia y sin recuperación de contraseña automatizada. Si pierde la contraseña, no puede acceder. Si pierde acceso al email o al método de reseteo manual (base de datos), queda bloqueado.

**Probabilidad:** Baja.

**Impacto:** Alto. Nadie puede registrar resultados hasta que se resuelva.

**Mitigación:** Documentar el proceso de reseteo manual de contraseña directamente en la base de datos (UPDATE con nuevo hash bcrypt). Almacenar las credenciales en un gestor de contraseñas. Para el futuro, considerar agregar recuperación por email.

## R-06 — Curva de aprendizaje y riesgo de abandono

**Riesgo:** Es el primer proyecto de software del desarrollador. La combinación de tecnologías nuevas (FastAPI, React, PostgreSQL, JWT, despliegue en cloud) puede generar bloqueos frecuentes que acumulen frustración y lleven al abandono del proyecto.

**Probabilidad:** Media.

**Impacto:** Crítico. El proyecto no se termina.

**Mitigación:** Seguir estrictamente el roadmap de implementación, priorizando victorias tempranas que generen motivación (ver algo funcionando lo antes posible). Usar agentes de desarrollo (Claude Code u otros) para desbloquear problemas técnicos rápido. Mantener el scope del MVP estricto — resistir la tentación de agregar features antes de que lo básico funcione.

## R-07 — Scope creep

**Riesgo:** Durante la planificación ya surgieron ideas que se descartaron del MVP (fotos, recordatorios, vista histórica, agente configurador). Durante la implementación surgirán más. Cada feature adicional retrasa el MVP y aumenta la complejidad.

**Probabilidad:** Alta.

**Impacto:** Medio. No rompe nada técnicamente, pero puede impedir que el MVP salga a tiempo.

**Mitigación:** Mantener una lista explícita de "features para después" y agregar ahí cada idea nueva sin discutirla en detalle. Solo se implementa lo que está en los casos de uso aprobados (CU-01 a CU-08). Cualquier adición requiere revisar el impacto en el roadmap antes de aceptarla.
