"""
locales.py
===========
Module de traduction centralisé (i18n) de l'application. Toute chaîne
affichée à l'écran (ou dans le PDF) passe par la fonction `t(cle)`
plutôt que d'être écrite en dur dans une page -- ainsi, ajouter une
langue ou corriger un texte se fait à un seul endroit.

Fonctionnement :
    - `TRADUCCIONES` est un dictionnaire {langue: {cle: texte}}.
    - `t(cle, **kwargs)` lit la langue active dans st.session_state et
      renvoie le texte correspondant, avec un `.format(**kwargs)` pour
      les textes qui contiennent des paramètres (ex: "{fecha}").
    - Si une clé manque dans une langue, on retombe sur l'espagnol
      (langue par défaut) puis, en dernier recours, sur la clé elle-
      même -- l'app ne plante jamais pour une traduction manquante,
      elle affiche juste un texte moins joli le temps de la corriger.
"""

from __future__ import annotations

import streamlit as st

IDIOMA_DEFECTO = "es"

IDIOMAS_DISPONIBLES = {
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "en": "🇬🇧 English",
}

TRADUCCIONES: dict[str, dict[str, str]] = {
    "es": {
        # --- Común -----------------------------------------------------
        "common.app_name": "Centropuertas",
        "common.app_tagline": "Partes de Trabajo",
        "common.footer": "Montaje y mantenimiento de puertas automáticas",
        "common.guardar": "Guardar",
        "common.cancelar": "Cancelar",
        "common.anadir": "Añadir",
        "common.editar": "Editar",
        "common.eliminar": "Eliminar",
        "common.buscar": "Buscar",
        "common.todos": "(Todos)",
        "common.ninguno": "(Ninguno)",
        "common.si": "Sí",
        "common.no": "No",

        # --- Autenticación -------------------------------------------------
        "auth.titulo": "Centropuertas",
        "auth.subtitulo": "Accede con tu usuario y contraseña de técnico.",
        "auth.usuario": "Usuario",
        "auth.contrasena": "Contraseña",
        "auth.entrar": "Entrar",
        "auth.error_credenciales": "Usuario o contraseña incorrectos.",
        "auth.credenciales_prueba": "Usuario de prueba: {login} · Contraseña: {password} (cámbiala cuanto antes desde una cuenta real).",
        "auth.sesion_como": "👤 {nombre}",
        "auth.cerrar_sesion": "Cerrar sesión",

        # --- Navegación --------------------------------------------------
        "nav.nuevo_parte": "Nuevo Parte",
        "nav.referencias": "Referencias",
        "nav.dashboard": "Dashboard (Totales)",
        "nav.historial": "Historial & PDF",
        "nav.ajustes": "Ajustes",

        # --- Tipos de jornada --------------------------------------------
        "tipo.Trabajo": "Trabajo",
        "tipo.Vacaciones": "Vacaciones",
        "tipo.Baja": "Baja",
        "tipo.Guardia": "Guardia",
        "tipo.Festivo": "Festivo",

        # --- Nuevo Parte ---------------------------------------------------
        "nuevo_parte.titulo": "Nuevo Parte Diario",
        "nuevo_parte.subtitulo": "Registra tu jornada de hoy: horas, dietas, cliente y trabajo realizado.",
        "nuevo_parte.fecha": "Fecha",
        "nuevo_parte.tipo_jornada": "Tipo de jornada",
        "nuevo_parte.ya_existe": "Ya existe un parte guardado para el {fecha}. Los campos se han rellenado con esos datos; puedes modificarlos y volver a guardar.",
        "nuevo_parte.horas_dietas": "⏱️ Horas y dietas",
        "nuevo_parte.horas_normales": "Horas normales",
        "nuevo_parte.horas_extra": "Horas extra",
        "nuevo_parte.dietas": "Dietas (nº)",
        "nuevo_parte.detalle_trabajo": "🔧 Detalle del trabajo",
        "nuevo_parte.cliente": "Cliente",
        "nuevo_parte.sin_cliente": "(sin cliente)",
        "nuevo_parte.tipo_intervencion": "Tipo de intervención",
        "nuevo_parte.sin_intervencion": "(sin tipo)",
        "nuevo_parte.descripcion": "Descripción del trabajo realizado",
        "nuevo_parte.descripcion_placeholder": "Ej. Instalación de puerta seccional, ajuste de fotocélulas GEZE...",
        "nuevo_parte.observaciones": "Observaciones / Problemas",
        "nuevo_parte.observaciones_placeholder": "Ej. Cruce de cuerdas en el eje, motor con ruido anómalo...",
        "nuevo_parte.colega": "Compañero asignado",
        "nuevo_parte.sin_colega": "(sin compañero)",
        "nuevo_parte.guardar_parte": "💾 Guardar parte del día",
        "nuevo_parte.guardado_ok": "Parte del {fecha} guardado correctamente.",
        "nuevo_parte.sin_referencias_aviso": "Aún no has creado ningún {tipo} en \"Referencias\" — puedes dejarlo en blanco por ahora y añadirlo más tarde.",

        # --- Referencias -----------------------------------------------
        "referencias.titulo": "Referencias",
        "referencias.subtitulo": "Gestiona los clientes, tipos de intervención y compañeros usados en los partes.",
        "referencias.tab_clientes": "Clientes",
        "referencias.tab_tipos": "Tipos de Intervención",
        "referencias.tab_colegas": "Compañeros",
        "referencias.nuevo_cliente": "➕ Nuevo cliente",
        "referencias.nuevo_tipo": "➕ Nuevo tipo de intervención",
        "referencias.nuevo_colega": "➕ Nuevo compañero",
        "referencias.nombre": "Nombre",
        "referencias.direccion": "Dirección",
        "referencias.telefono": "Teléfono",
        "referencias.notas": "Notas",
        "referencias.lista_vacia": "Todavía no hay ninguno. Añade el primero arriba.",
        "referencias.nombre_obligatorio": "El nombre es obligatorio.",
        "referencias.creado_ok": "Añadido correctamente.",
        "referencias.actualizado_ok": "Actualizado correctamente.",
        "referencias.eliminado_ok": "Eliminado correctamente.",
        "referencias.confirmar_eliminar_titulo": "¿Eliminar \"{nombre}\"?",
        "referencias.confirmar_eliminar_texto": "Los partes ya guardados que lo usan no se borrarán, solo quedará esa referencia vacía.",
        "referencias.confirmar_eliminar_boton": "Sí, eliminar",

        # --- Dashboard ---------------------------------------------------
        "dashboard.titulo": "Dashboard Anual",
        "dashboard.subtitulo": "Totales automáticos del año: horas, extras, dietas y vacaciones.",
        "dashboard.anio": "Año",
        "dashboard.horas_trabajadas": "Horas trabajadas",
        "dashboard.horas_extra": "Horas extra",
        "dashboard.dietas": "Dietas",
        "dashboard.vacaciones_consumidas": "Vacaciones consumidas",
        "dashboard.vacaciones_pendientes": "Vacaciones pendientes",
        "dashboard.dias_baja": "Días de baja",
        "dashboard.dias_guardia": "Días de guardia",
        "dashboard.progreso_convenio": "Progreso sobre el convenio anual ({horas_convenio:g} h)",
        "dashboard.sin_datos": "Todavía no hay partes registrados para este año.",
        "dashboard.grafico_horas": "Horas trabajadas vs. horas extra por mes",
        "dashboard.grafico_dietas": "Evolución de dietas por mes",
        "dashboard.de_dias": "de {dias} días asignados al año",

        # --- Historial -----------------------------------------------------
        "historial.titulo": "Historial & Informes",
        "historial.subtitulo": "Consulta, edita y exporta los partes guardados.",
        "historial.tab_mes": "Vista mensual",
        "historial.tab_buscador": "🔎 Buscador",
        "historial.tab_conocimiento": "🧠 Base de Conocimientos",
        "historial.conocimiento_subtitulo": "Busca en todo el histórico por palabra clave o por tipo de intervención — útil para localizar un problema recurrente (ej. cables cruzados en sensores GEZE) y ver cómo se resolvió antes.",
        "historial.mes": "Mes",
        "historial.generar_informe": "📄 Generar Informe Mensual PDF",
        "historial.exportar_excel": "📊 Exportar a Excel",
        "historial.palabra_clave": "Palabra clave (descripción u observaciones)",
        "historial.filtro_cliente": "Cliente",
        "historial.filtro_colega": "Compañero",
        "historial.filtro_intervencion": "Tipo de intervención",
        "historial.filtro_anio": "Año",
        "historial.resultados_encontrados": "{n} resultado(s) encontrado(s).",
        "historial.sin_resultados_conocimiento": "Escribe una palabra clave o elige un tipo de intervención para buscar en el histórico.",
        "historial.sin_partes_mes": "Todavía no hay partes guardados para este mes.",
        "historial.horas": "Horas",
        "historial.h_extra_card": "+ {h:g} h extra",
        "historial.dietas_card": "{n:g} dieta(s)",

        # --- Ajustes -------------------------------------------------------
        "ajustes.titulo": "Ajustes",
        "ajustes.subtitulo": "Idioma, año en curso y configuración global.",
        "ajustes.idioma": "Idioma",
        "ajustes.datos_trabajador": "👤 Datos del trabajador",
        "ajustes.nombre_trabajador": "Nombre y apellidos",
        "ajustes.empresa": "Empresa",
        "ajustes.nif_cif": "NIF/CIF",
        "ajustes.config_global": "🌍 Configuración global",
        "ajustes.anio_actual": "Año en curso",
        "ajustes.horas_convenio_anual": "Horas de convenio anuales",
        "ajustes.dias_vacaciones_anuales": "Días de vacaciones anuales",
        "ajustes.guardado_ok": "Configuración actualizada.",
        "ajustes.backup": "💾 Copia de seguridad",
        "ajustes.backup_desc": "Descarga el fichero de base de datos completo (todos los clientes, tipos, compañeros y partes).",
        "ajustes.descargar_backup": "⬇️ Descargar copia de seguridad",
        "ajustes.instalar_app": "📲 Instalar en el móvil",
        "ajustes.instalar_app_desc": "Instala CentroPuertas como aplicación en tu teléfono u ordenador para abrirla con un icono, sin pasar por el navegador.",
        "ajustes.instalar_app_boton": "Instalar aplicación",
        "ajustes.instalar_app_hecho": "Aplicación instalada.",
        "ajustes.instalar_app_ios": "En iPhone/iPad (Safari): pulsa el botón Compartir y elige \"Añadir a pantalla de inicio\" — Safari no muestra un botón automático como Android.",

        # --- PDF -----------------------------------------------------------
        "pdf.titulo_parte": "Parte de Trabajo Mensual",
        "pdf.resumen": "Resumen del mes",
        "pdf.firma": "Firma del trabajador/a",
        "pdf.fecha_firma": "Fecha",
        "pdf.col_fecha": "Fecha",
        "pdf.col_tipo": "Tipo",
        "pdf.col_horas": "Horas",
        "pdf.col_extra": "H. Extra",
        "pdf.col_dietas": "Dietas",
        "pdf.col_cliente": "Cliente",
        "pdf.col_intervencion": "Intervención",
        "pdf.col_descripcion": "Trabajo realizado",
        "pdf.col_observaciones": "Observaciones",
        "pdf.col_colega": "Compañero",

        # --- Meses / días de la semana ------------------------------------
        "mes.1": "Enero", "mes.2": "Febrero", "mes.3": "Marzo", "mes.4": "Abril",
        "mes.5": "Mayo", "mes.6": "Junio", "mes.7": "Julio", "mes.8": "Agosto",
        "mes.9": "Septiembre", "mes.10": "Octubre", "mes.11": "Noviembre", "mes.12": "Diciembre",
        "dia.0": "Lunes", "dia.1": "Martes", "dia.2": "Miércoles", "dia.3": "Jueves",
        "dia.4": "Viernes", "dia.5": "Sábado", "dia.6": "Domingo",
    },

    "fr": {
        "common.app_name": "Centropuertas",
        "common.app_tagline": "Partes de Travail",
        "common.footer": "Montage et maintenance de portes automatiques",
        "common.guardar": "Enregistrer",
        "common.cancelar": "Annuler",
        "common.anadir": "Ajouter",
        "common.editar": "Modifier",
        "common.eliminar": "Supprimer",
        "common.buscar": "Rechercher",
        "common.todos": "(Tous)",
        "common.ninguno": "(Aucun)",
        "common.si": "Oui",
        "common.no": "Non",

        "auth.titulo": "Centropuertas",
        "auth.subtitulo": "Connecte-toi avec ton identifiant et ton mot de passe technicien.",
        "auth.usuario": "Identifiant",
        "auth.contrasena": "Mot de passe",
        "auth.entrar": "Se connecter",
        "auth.error_credenciales": "Identifiant ou mot de passe incorrect.",
        "auth.credenciales_prueba": "Compte de test : {login} · Mot de passe : {password} (à changer dès que possible pour un vrai compte).",
        "auth.sesion_como": "👤 {nombre}",
        "auth.cerrar_sesion": "Se déconnecter",

        "nav.nuevo_parte": "Nouveau Parte",
        "nav.referencias": "Références",
        "nav.dashboard": "Tableau de bord (Totaux)",
        "nav.historial": "Historique & PDF",
        "nav.ajustes": "Paramètres",

        "tipo.Trabajo": "Travail",
        "tipo.Vacaciones": "Vacances",
        "tipo.Baja": "Arrêt maladie",
        "tipo.Guardia": "Garde",
        "tipo.Festivo": "Jour férié",

        "nuevo_parte.titulo": "Nouveau Parte Journalier",
        "nuevo_parte.subtitulo": "Enregistre ta journée : heures, indemnités, client et travail effectué.",
        "nuevo_parte.fecha": "Date",
        "nuevo_parte.tipo_jornada": "Type de journée",
        "nuevo_parte.ya_existe": "Un parte existe déjà pour le {fecha}. Les champs ont été pré-remplis avec ces données ; tu peux les modifier et enregistrer à nouveau.",
        "nuevo_parte.horas_dietas": "⏱️ Heures et indemnités",
        "nuevo_parte.horas_normales": "Heures normales",
        "nuevo_parte.horas_extra": "Heures supplémentaires",
        "nuevo_parte.dietas": "Indemnités (nb)",
        "nuevo_parte.detalle_trabajo": "🔧 Détail du travail",
        "nuevo_parte.cliente": "Client",
        "nuevo_parte.sin_cliente": "(aucun client)",
        "nuevo_parte.tipo_intervencion": "Type d'intervention",
        "nuevo_parte.sin_intervencion": "(aucun type)",
        "nuevo_parte.descripcion": "Description du travail effectué",
        "nuevo_parte.descripcion_placeholder": "Ex. Installation de porte sectionnelle, réglage de cellules GEZE...",
        "nuevo_parte.observaciones": "Observations / Problèmes",
        "nuevo_parte.observaciones_placeholder": "Ex. Croisement de câbles sur l'axe, moteur bruyant...",
        "nuevo_parte.colega": "Collègue assigné",
        "nuevo_parte.sin_colega": "(aucun collègue)",
        "nuevo_parte.guardar_parte": "💾 Enregistrer le parte du jour",
        "nuevo_parte.guardado_ok": "Parte du {fecha} enregistré avec succès.",
        "nuevo_parte.sin_referencias_aviso": "Tu n'as encore créé aucun {tipo} dans \"Références\" — tu peux laisser ce champ vide pour l'instant et l'ajouter plus tard.",

        "referencias.titulo": "Références",
        "referencias.subtitulo": "Gère les clients, types d'intervention et collègues utilisés dans les partes.",
        "referencias.tab_clientes": "Clients",
        "referencias.tab_tipos": "Types d'Intervention",
        "referencias.tab_colegas": "Collègues",
        "referencias.nuevo_cliente": "➕ Nouveau client",
        "referencias.nuevo_tipo": "➕ Nouveau type d'intervention",
        "referencias.nuevo_colega": "➕ Nouveau collègue",
        "referencias.nombre": "Nom",
        "referencias.direccion": "Adresse",
        "referencias.telefono": "Téléphone",
        "referencias.notas": "Notes",
        "referencias.lista_vacia": "Il n'y en a encore aucun. Ajoute le premier ci-dessus.",
        "referencias.nombre_obligatorio": "Le nom est obligatoire.",
        "referencias.creado_ok": "Ajouté avec succès.",
        "referencias.actualizado_ok": "Mis à jour avec succès.",
        "referencias.eliminado_ok": "Supprimé avec succès.",
        "referencias.confirmar_eliminar_titulo": "Supprimer « {nombre} » ?",
        "referencias.confirmar_eliminar_texto": "Les partes déjà enregistrés qui l'utilisent ne seront pas supprimés, seule cette référence deviendra vide.",
        "referencias.confirmar_eliminar_boton": "Oui, supprimer",

        "dashboard.titulo": "Tableau de bord Annuel",
        "dashboard.subtitulo": "Totaux automatiques de l'année : heures, heures sup, indemnités et vacances.",
        "dashboard.anio": "Année",
        "dashboard.horas_trabajadas": "Heures travaillées",
        "dashboard.horas_extra": "Heures supplémentaires",
        "dashboard.dietas": "Indemnités",
        "dashboard.vacaciones_consumidas": "Vacances prises",
        "dashboard.vacaciones_pendientes": "Vacances restantes",
        "dashboard.dias_baja": "Jours d'arrêt maladie",
        "dashboard.dias_guardia": "Jours de garde",
        "dashboard.progreso_convenio": "Progression sur la convention annuelle ({horas_convenio:g} h)",
        "dashboard.sin_datos": "Il n'y a pas encore de parte enregistré pour cette année.",
        "dashboard.grafico_horas": "Heures travaillées vs. heures sup par mois",
        "dashboard.grafico_dietas": "Évolution des indemnités par mois",
        "dashboard.de_dias": "sur {dias} jours attribués par an",

        "historial.titulo": "Historique & Rapports",
        "historial.subtitulo": "Consulte, modifie et exporte les partes enregistrés.",
        "historial.tab_mes": "Vue mensuelle",
        "historial.tab_buscador": "🔎 Recherche",
        "historial.tab_conocimiento": "🧠 Base de Connaissances",
        "historial.conocimiento_subtitulo": "Recherche dans tout l'historique par mot-clé ou par type d'intervention -- utile pour retrouver un problème récurrent (ex. câbles croisés sur capteurs GEZE) et voir comment il a été résolu auparavant.",
        "historial.mes": "Mois",
        "historial.generar_informe": "📄 Générer Rapport Mensuel PDF",
        "historial.exportar_excel": "📊 Exporter en Excel",
        "historial.palabra_clave": "Mot-clé (description ou observations)",
        "historial.filtro_cliente": "Client",
        "historial.filtro_colega": "Collègue",
        "historial.filtro_intervencion": "Type d'intervention",
        "historial.filtro_anio": "Année",
        "historial.resultados_encontrados": "{n} résultat(s) trouvé(s).",
        "historial.sin_resultados_conocimiento": "Saisis un mot-clé ou choisis un type d'intervention pour rechercher dans l'historique.",
        "historial.sin_partes_mes": "Il n'y a pas encore de parte enregistré pour ce mois.",
        "historial.horas": "Heures",
        "historial.h_extra_card": "+ {h:g} h sup",
        "historial.dietas_card": "{n:g} indemnité(s)",

        "ajustes.titulo": "Paramètres",
        "ajustes.subtitulo": "Langue, année en cours et configuration globale.",
        "ajustes.idioma": "Langue",
        "ajustes.datos_trabajador": "👤 Données du travailleur",
        "ajustes.nombre_trabajador": "Nom et prénom",
        "ajustes.empresa": "Entreprise",
        "ajustes.nif_cif": "NIF/CIF (numéro fiscal)",
        "ajustes.config_global": "🌍 Configuration globale",
        "ajustes.anio_actual": "Année en cours",
        "ajustes.horas_convenio_anual": "Heures de convention annuelles",
        "ajustes.dias_vacaciones_anuales": "Jours de vacances annuels",
        "ajustes.guardado_ok": "Configuration mise à jour.",
        "ajustes.backup": "💾 Sauvegarde",
        "ajustes.backup_desc": "Télécharge le fichier de base de données complet (clients, types, collègues et partes).",
        "ajustes.descargar_backup": "⬇️ Télécharger la sauvegarde",
        "ajustes.instalar_app": "📲 Installer sur mobile",
        "ajustes.instalar_app_desc": "Installe CentroPuertas comme une application sur ton téléphone ou ordinateur, avec sa propre icône, sans passer par le navigateur.",
        "ajustes.instalar_app_boton": "Installer l'application",
        "ajustes.instalar_app_hecho": "Application installée.",
        "ajustes.instalar_app_ios": "Sur iPhone/iPad (Safari) : appuie sur le bouton Partager puis choisis \"Sur l'écran d'accueil\" -- Safari n'affiche pas de bouton automatique comme Android.",

        "pdf.titulo_parte": "Parte de Travail Mensuel",
        "pdf.resumen": "Résumé du mois",
        "pdf.firma": "Signature du travailleur",
        "pdf.fecha_firma": "Date",
        "pdf.col_fecha": "Date",
        "pdf.col_tipo": "Type",
        "pdf.col_horas": "Heures",
        "pdf.col_extra": "H. Sup",
        "pdf.col_dietas": "Indemnités",
        "pdf.col_cliente": "Client",
        "pdf.col_intervencion": "Intervention",
        "pdf.col_descripcion": "Travail effectué",
        "pdf.col_observaciones": "Observations",
        "pdf.col_colega": "Collègue",

        "mes.1": "Janvier", "mes.2": "Février", "mes.3": "Mars", "mes.4": "Avril",
        "mes.5": "Mai", "mes.6": "Juin", "mes.7": "Juillet", "mes.8": "Août",
        "mes.9": "Septembre", "mes.10": "Octobre", "mes.11": "Novembre", "mes.12": "Décembre",
        "dia.0": "Lundi", "dia.1": "Mardi", "dia.2": "Mercredi", "dia.3": "Jeudi",
        "dia.4": "Vendredi", "dia.5": "Samedi", "dia.6": "Dimanche",
    },

    "en": {
        "common.app_name": "Centropuertas",
        "common.app_tagline": "Work Log",
        "common.footer": "Automatic door installation and maintenance",
        "common.guardar": "Save",
        "common.cancelar": "Cancel",
        "common.anadir": "Add",
        "common.editar": "Edit",
        "common.eliminar": "Delete",
        "common.buscar": "Search",
        "common.todos": "(All)",
        "common.ninguno": "(None)",
        "common.si": "Yes",
        "common.no": "No",

        "auth.titulo": "Centropuertas",
        "auth.subtitulo": "Log in with your technician username and password.",
        "auth.usuario": "Username",
        "auth.contrasena": "Password",
        "auth.entrar": "Log in",
        "auth.error_credenciales": "Incorrect username or password.",
        "auth.credenciales_prueba": "Test account: {login} · Password: {password} (change it as soon as possible for a real account).",
        "auth.sesion_como": "👤 {nombre}",
        "auth.cerrar_sesion": "Log out",

        "nav.nuevo_parte": "New Entry",
        "nav.referencias": "References",
        "nav.dashboard": "Dashboard (Totals)",
        "nav.historial": "History & PDF",
        "nav.ajustes": "Settings",

        "tipo.Trabajo": "Work",
        "tipo.Vacaciones": "Vacation",
        "tipo.Baja": "Sick leave",
        "tipo.Guardia": "On-call",
        "tipo.Festivo": "Holiday",

        "nuevo_parte.titulo": "New Daily Entry",
        "nuevo_parte.subtitulo": "Log today's work day: hours, allowances, client and work performed.",
        "nuevo_parte.fecha": "Date",
        "nuevo_parte.tipo_jornada": "Day type",
        "nuevo_parte.ya_existe": "An entry already exists for {fecha}. The fields have been pre-filled with that data; you can edit them and save again.",
        "nuevo_parte.horas_dietas": "⏱️ Hours and allowances",
        "nuevo_parte.horas_normales": "Regular hours",
        "nuevo_parte.horas_extra": "Overtime hours",
        "nuevo_parte.dietas": "Allowances (No.)",
        "nuevo_parte.detalle_trabajo": "🔧 Work details",
        "nuevo_parte.cliente": "Client",
        "nuevo_parte.sin_cliente": "(no client)",
        "nuevo_parte.tipo_intervencion": "Intervention type",
        "nuevo_parte.sin_intervencion": "(no type)",
        "nuevo_parte.descripcion": "Description of work performed",
        "nuevo_parte.descripcion_placeholder": "E.g. Sectional door installation, GEZE sensor adjustment...",
        "nuevo_parte.observaciones": "Observations / Issues",
        "nuevo_parte.observaciones_placeholder": "E.g. Crossed cables on the shaft, motor making unusual noise...",
        "nuevo_parte.colega": "Assigned colleague",
        "nuevo_parte.sin_colega": "(no colleague)",
        "nuevo_parte.guardar_parte": "💾 Save day entry",
        "nuevo_parte.guardado_ok": "Entry for {fecha} saved successfully.",
        "nuevo_parte.sin_referencias_aviso": "You haven't created any {tipo} in \"References\" yet — you can leave this blank for now and add it later.",

        "referencias.titulo": "References",
        "referencias.subtitulo": "Manage the clients, intervention types and colleagues used in entries.",
        "referencias.tab_clientes": "Clients",
        "referencias.tab_tipos": "Intervention Types",
        "referencias.tab_colegas": "Colleagues",
        "referencias.nuevo_cliente": "➕ New client",
        "referencias.nuevo_tipo": "➕ New intervention type",
        "referencias.nuevo_colega": "➕ New colleague",
        "referencias.nombre": "Name",
        "referencias.direccion": "Address",
        "referencias.telefono": "Phone",
        "referencias.notas": "Notes",
        "referencias.lista_vacia": "None yet. Add the first one above.",
        "referencias.nombre_obligatorio": "Name is required.",
        "referencias.creado_ok": "Added successfully.",
        "referencias.actualizado_ok": "Updated successfully.",
        "referencias.eliminado_ok": "Deleted successfully.",
        "referencias.confirmar_eliminar_titulo": "Delete \"{nombre}\"?",
        "referencias.confirmar_eliminar_texto": "Entries that already use it will not be deleted, only this reference will become empty.",
        "referencias.confirmar_eliminar_boton": "Yes, delete",

        "dashboard.titulo": "Annual Dashboard",
        "dashboard.subtitulo": "Automatic yearly totals: hours, overtime, allowances and vacation.",
        "dashboard.anio": "Year",
        "dashboard.horas_trabajadas": "Hours worked",
        "dashboard.horas_extra": "Overtime hours",
        "dashboard.dietas": "Allowances",
        "dashboard.vacaciones_consumidas": "Vacation taken",
        "dashboard.vacaciones_pendientes": "Vacation remaining",
        "dashboard.dias_baja": "Sick leave days",
        "dashboard.dias_guardia": "On-call days",
        "dashboard.progreso_convenio": "Progress vs. annual agreement ({horas_convenio:g} h)",
        "dashboard.sin_datos": "No entries recorded yet for this year.",
        "dashboard.grafico_horas": "Hours worked vs. overtime by month",
        "dashboard.grafico_dietas": "Allowances trend by month",
        "dashboard.de_dias": "out of {dias} days allotted per year",

        "historial.titulo": "History & Reports",
        "historial.subtitulo": "Browse, edit and export saved entries.",
        "historial.tab_mes": "Monthly view",
        "historial.tab_buscador": "🔎 Search",
        "historial.tab_conocimiento": "🧠 Knowledge Base",
        "historial.conocimiento_subtitulo": "Search the whole history by keyword or intervention type -- useful for finding a recurring problem (e.g. crossed cables on GEZE sensors) and seeing how it was solved before.",
        "historial.mes": "Month",
        "historial.generar_informe": "📄 Generate Monthly PDF Report",
        "historial.exportar_excel": "📊 Export to Excel",
        "historial.palabra_clave": "Keyword (description or notes)",
        "historial.filtro_cliente": "Client",
        "historial.filtro_colega": "Colleague",
        "historial.filtro_intervencion": "Intervention type",
        "historial.filtro_anio": "Year",
        "historial.resultados_encontrados": "{n} result(s) found.",
        "historial.sin_resultados_conocimiento": "Type a keyword or choose an intervention type to search the history.",
        "historial.sin_partes_mes": "No entries saved yet for this month.",
        "historial.horas": "Hours",
        "historial.h_extra_card": "+ {h:g} h overtime",
        "historial.dietas_card": "{n:g} allowance(s)",

        "ajustes.titulo": "Settings",
        "ajustes.subtitulo": "Language, current year and global configuration.",
        "ajustes.idioma": "Language",
        "ajustes.datos_trabajador": "👤 Worker details",
        "ajustes.nombre_trabajador": "Full name",
        "ajustes.empresa": "Company",
        "ajustes.nif_cif": "Tax ID (NIF/CIF)",
        "ajustes.config_global": "🌍 Global configuration",
        "ajustes.anio_actual": "Current year",
        "ajustes.horas_convenio_anual": "Annual agreement hours",
        "ajustes.dias_vacaciones_anuales": "Annual vacation days",
        "ajustes.guardado_ok": "Configuration updated.",
        "ajustes.backup": "💾 Backup",
        "ajustes.backup_desc": "Download the full database file (clients, types, colleagues and entries).",
        "ajustes.descargar_backup": "⬇️ Download backup",
        "ajustes.instalar_app": "📲 Install on mobile",
        "ajustes.instalar_app_desc": "Install CentroPuertas as an app on your phone or computer, with its own icon, without going through the browser.",
        "ajustes.instalar_app_boton": "Install app",
        "ajustes.instalar_app_hecho": "App installed.",
        "ajustes.instalar_app_ios": "On iPhone/iPad (Safari): tap the Share button and choose \"Add to Home Screen\" -- Safari doesn't show an automatic button like Android.",

        "pdf.titulo_parte": "Monthly Work Report",
        "pdf.resumen": "Month summary",
        "pdf.firma": "Employee signature",
        "pdf.fecha_firma": "Date",
        "pdf.col_fecha": "Date",
        "pdf.col_tipo": "Type",
        "pdf.col_horas": "Hours",
        "pdf.col_extra": "Overtime",
        "pdf.col_dietas": "Allowances",
        "pdf.col_cliente": "Client",
        "pdf.col_intervencion": "Intervention",
        "pdf.col_descripcion": "Work performed",
        "pdf.col_observaciones": "Observations",
        "pdf.col_colega": "Colleague",

        "mes.1": "January", "mes.2": "February", "mes.3": "March", "mes.4": "April",
        "mes.5": "May", "mes.6": "June", "mes.7": "July", "mes.8": "August",
        "mes.9": "September", "mes.10": "October", "mes.11": "November", "mes.12": "December",
        "dia.0": "Monday", "dia.1": "Tuesday", "dia.2": "Wednesday", "dia.3": "Thursday",
        "dia.4": "Friday", "dia.5": "Saturday", "dia.6": "Sunday",
    },
}


def get_idioma_activo() -> str:
    """Langue active pour cette session (par défaut : espagnol)."""
    return st.session_state.get("idioma", IDIOMA_DEFECTO)


def set_idioma_activo(idioma: str) -> None:
    """Change la langue active pour le reste de la session."""
    if idioma in TRADUCCIONES:
        st.session_state["idioma"] = idioma


def t(clave: str, **kwargs) -> str:
    """
    Traduit `clave` dans la langue active. Les `kwargs` sont injectés
    dans le texte via `.format()`, ex : t("nuevo_parte.guardado_ok",
    fecha="08/08/2026") -> "Parte del 08/08/2026 guardado correctamente."
    """
    idioma = get_idioma_activo()
    texto = TRADUCCIONES.get(idioma, {}).get(clave)
    if texto is None:
        texto = TRADUCCIONES[IDIOMA_DEFECTO].get(clave, clave)
    if kwargs:
        try:
            return texto.format(**kwargs)
        except (KeyError, IndexError):
            return texto
    return texto


def t_tipo_jornada(tipo: str) -> str:
    """Traduit une valeur de l'enum tipo_jornada (ex: 'Trabajo')."""
    return t(f"tipo.{tipo}")


def t_mes(numero: int) -> str:
    """Traduit un numéro de mois (1-12) en son nom dans la langue active."""
    return t(f"mes.{numero}")


def t_dia_semana(indice: int) -> str:
    """Traduit un indice de jour de semaine (0=Lundi ... 6=Dimanche, comme date.weekday())."""
    return t(f"dia.{indice}")
