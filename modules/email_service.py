"""
Service d'envoi d'emails avec Gmail SMTP
"""
import smtplib
import os
import logging
from email.message import EmailMessage

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = os.environ.get('GMAIL_EMAIL')
        self.password = os.environ.get('GMAIL_APP_PASSWORD')
        
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Envoie un email via Gmail SMTP"""
        try:
            # Créer le message
            msg = EmailMessage()
            msg['From'] = f'MindTraderPro <{self.email}>'
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Ajouter le contenu HTML
            msg.set_content(text_content or "Version texte de l'email")
            msg.add_alternative(html_content, subtype='html')
            
            # Connexion SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            
            # Envoyer l'email
            server.send_message(msg)
            server.quit()
            
            logging.info(f"Email envoyé avec succès à {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de l'email à {to_email}: {str(e)}")
            return False
    
    def send_validation_email(self, to_email, user_name, validation_link):
        """Envoie un email de validation de compte"""
        subject = "Validez votre compte MindTraderPro"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Validation de compte - MindTraderPro</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .button {{
                    display: inline-block;
                    background: #007bff;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Bienvenue sur MindTraderPro !</h1>
            </div>
            <div class="content">
                <h2>Bonjour {user_name} !</h2>
                <p>Merci de vous être inscrit sur <strong>MindTraderPro</strong>, votre plateforme de trading intelligente.</p>
                
                <p>Pour activer votre compte et accéder à toutes nos fonctionnalités, veuillez cliquer sur le bouton ci-dessous :</p>
                
                <div style="text-align: center;">
                    <a href="{validation_link}" class="button">
                        ✅ Valider mon compte
                    </a>
                </div>
                
                <p>Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :</p>
                <p style="background: #e9ecef; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {validation_link}
                </p>
                
                <h3>🎯 Ce qui vous attend :</h3>
                <ul>
                    <li>✅ Calculateur de lots intelligent</li>
                    <li>✅ Gestion avancée du risque</li>
                    <li>✅ Journal de trading professionnel</li>
                    <li>✅ Assistant IA personnalisé</li>
                </ul>
                
                <p><strong>Important :</strong> Ce lien expire dans 24 heures pour votre sécurité.</p>
            </div>
            <div class="footer">
                <p>Cet email a été envoyé par MindTraderPro</p>
                <p>Si vous n'avez pas créé de compte, ignorez cet email.</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Bonjour {user_name} !
        
        Merci de vous être inscrit sur MindTraderPro.
        
        Pour valider votre compte, cliquez sur ce lien :
        {validation_link}
        
        Ce lien expire dans 24 heures.
        
        MindTraderPro - Votre plateforme de trading intelligente
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_welcome_email(self, to_email, user_name):
        """Envoie un email de bienvenue après validation"""
        subject = "🎉 Compte validé - Bienvenue dans MindTraderPro !"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    margin-top: 20px;
                    border-radius: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Félicitations {user_name} !</h1>
                <p>Votre compte est maintenant actif</p>
            </div>
            <div class="content">
                <h2>Prêt à commencer votre journey de trading ?</h2>
                <p>Votre compte MindTraderPro est maintenant validé et vous pouvez accéder à toutes nos fonctionnalités :</p>
                
                <h3>🚀 Commencez dès maintenant :</h3>
                <ul>
                    <li>📊 Utilisez notre calculateur de lots intelligent</li>
                    <li>🛡️ Configurez votre gestion du risque</li>
                    <li>📝 Tenez votre journal de trading</li>
                    <li>🤖 Discutez avec notre assistant IA</li>
                </ul>
                
                <p>Bonne trading et bienvenue dans la communauté MindTraderPro !</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)

# Instance globale du service email
email_service = EmailService()