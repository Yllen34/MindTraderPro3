# Trading Risk Calculator

## Overview

This is a Flask-based web application that provides a professional XAUUSD (Gold/USD) trading risk calculator. The application helps traders calculate optimal lot sizes based on risk management principles, taking into account their capital, risk percentage, and stop-loss levels.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Pure HTML/CSS/JavaScript with Bootstrap 5 dark theme
- **UI Components**: Responsive card-based layout with real-time form validation
- **Styling**: CSS custom properties for consistent theming with trading-specific color schemes (green for buy, red for sell)
- **JavaScript**: Vanilla JS class-based architecture for calculator functionality

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Structure**: Simple MVC pattern with main application logic in `app.py`
- **Entry Point**: `main.py` imports and serves the Flask app
- **Deployment**: Gunicorn WSGI server with auto-scaling deployment target

### Data Storage Solutions
- **Database**: PostgreSQL configured in the environment (though not actively used in current implementation)
- **ORM**: Flask-SQLAlchemy available but not implemented yet
- **Session Management**: Flask sessions with configurable secret key

### Authentication and Authorization
- **Current State**: No authentication implemented
- **Session Secret**: Environment-based configuration with development fallback

## Key Components

### Trading Calculator Engine
- **Core Logic**: Risk-based lot size calculation using fixed pip values
- **Configuration**: 
  - Default capital: $20,000
  - Default risk: 0.5%
  - Pip value: $10 per lot for XAUUSD
- **Calculation Method**: `risk_usd = capital * (risk_percent / 100)` and `lot_size = risk_usd / (sl_pips * pip_value)`

### Web Interface
- **Main Route**: Single-page application serving the calculator interface
- **Form Handling**: Real-time validation and calculation
- **Responsive Design**: Mobile-first approach with Bootstrap grid system

### External Bot Integration
- **Telegram Bot**: Separate bot implementation for automated trade analysis
- **Pattern Matching**: Regex-based parsing of trading signals
- **Response Format**: Markdown-formatted calculation results

## Data Flow

1. **User Input**: Trading parameters (direction, entry, stop-loss, capital, risk percentage)
2. **Validation**: Client-side validation with visual feedback
3. **Calculation**: Server-side risk calculation using trading formulas
4. **Response**: JSON response with lot size and risk metrics
5. **Display**: Dynamic UI updates showing calculated results

## External Dependencies

### Python Packages
- **Flask**: Web framework and templating
- **Flask-SQLAlchemy**: Database ORM (prepared for future use)
- **Gunicorn**: Production WSGI server
- **psycopg2-binary**: PostgreSQL database adapter
- **email-validator**: Input validation utilities

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome**: Icon library for enhanced UX
- **Custom CSS**: Trading-specific styling and animations

### Development Environment
- **Replit**: Cloud-based development platform
- **Nix**: Package management with Python 3.11 and PostgreSQL
- **UV**: Modern Python package manager for dependency resolution

## Deployment Strategy

### Platform Configuration
- **Target**: Autoscale deployment on Replit infrastructure
- **Server**: Gunicorn with host binding to 0.0.0.0:5000
- **Process Management**: Reuse-port and reload capabilities for development

### Environment Management
- **Configuration**: Environment variables for sensitive data
- **Secrets**: Session keys and API tokens stored securely
- **Database**: PostgreSQL configured but not actively used (ready for future features)

### Workflow Automation
- **Run Button**: Parallel workflow execution
- **Development Mode**: Auto-reload with port monitoring
- **Production Ready**: Gunicorn production server configuration

The application follows a simple but extensible architecture, making it easy to add features like user accounts, trade history, or additional trading pairs while maintaining the current risk calculation functionality.