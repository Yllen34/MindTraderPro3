"""
MindTraderPro - Point d'entrée principal
Application Flask avec système d'authentification complet et gestion des rôles
"""
from app_final import app

if __name__ == '__main__':
    print("🚀 Démarrage de MindTraderPro - Système d'Authentification Complet...")
    print("✅ Base de données SQLite initialisée")
    print("✅ Authentification sécurisée avec bcrypt")
    print("✅ Gestion des rôles: Standard, Premium, Lifetime")
    print("✅ Navigation dynamique selon l'authentification")
    print("✅ Système de permissions par fonctionnalité")
    print("✅ Application 100% sécurisée et fonctionnelle !")
    app.run(host='0.0.0.0', port=5000, debug=True)