#!/usr/bin/env python3
"""
Quick Start - Análisis de Matriz de Confusión
Script de inicio rápido para ejecutar análisis de clasificación de gestos
"""

import sys
import os
import argparse
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from gesture_confusion_analyzer import GestureConfusionAnalyzer
from real_model_analyzer import RealModelAnalyzer
from run_confusion_analysis import ConfusionAnalysisRunner


def show_banner():
    """Mostrar banner de bienvenida"""
    print("\n" + "="*80)
    print("🧠 GESTUREAI - ANÁLISIS DE MATRIZ DE CONFUSIÓN 🧠")
    print("="*80)
    print("Herramientas completas para análisis de clasificación de gestos")
    print("Incluye análisis sintético, modelo real y comparativas detalladas")
    print("="*80)


def run_quick_demo():
    """Ejecutar demo rápido"""
    print("\n🚀 EJECUTANDO DEMO RÁPIDO")
    print("="*40)
    
    analyzer = GestureConfusionAnalyzer()
    
    # Analizar top 3 controladores
    top_controllers = ['mouse', 'shortcuts', 'volume']
    
    for controller in top_controllers:
        print(f"\n📊 Analizando {controller.upper()}...")
        try:
            analysis = analyzer.analyze_controller(controller, samples_per_gesture=50)
            analyzer.visualize_confusion_matrix(controller)
            
            accuracy = analysis['metrics']['accuracy']
            print(f"✅ Precisión: {accuracy:.1%}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Demo completado! Revisa las carpetas 'reports' para ver los resultados.")


def run_full_synthetic_analysis():
    """Ejecutar análisis completo sintético"""
    print("\n🔍 ANÁLISIS COMPLETO SINTÉTICO")
    print("="*50)
    
    analyzer = GestureConfusionAnalyzer()
    
    try:
        results = analyzer.analyze_all_controllers()
        print(f"\n✅ Análisis completo finalizado")
        print(f"📊 Controladores analizados: {len(results['individual_analyses'])}")
        
        # Mostrar ranking
        comparative = results['comparative_analysis']
        print(f"\n🏆 RANKING DE PRECISIÓN:")
        for i, item in enumerate(comparative['accuracy_ranking'][:5], 1):
            controller = item['controller']
            accuracy = item['accuracy']
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
            print(f"{emoji} {i}. {controller.upper()}: {accuracy:.1%}")
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")


def run_real_model_analysis():
    """Ejecutar análisis con modelo real"""
    print("\n🤖 ANÁLISIS CON MODELO REAL DE MEDIAPIPE")
    print("="*60)
    
    analyzer = RealModelAnalyzer()
    
    if analyzer.gesture_recognizer is None:
        print("❌ No se pudo inicializar el modelo real")
        print("   Verifica que el archivo gesture_recognizer.task esté en models/")
        return
    
    try:
        print("🚀 Iniciando análisis con modelo real...")
        results = analyzer.analyze_real_gesture_recognition(num_samples_per_gesture=25)
        
        print("📊 Generando visualizaciones...")
        analyzer.visualize_real_model_results(results)
        
        print("📝 Generando reporte de calibración...")
        analyzer.generate_calibration_report(results)
        
        # Mostrar resumen
        overall_acc = results['overall_accuracy']
        total_samples = results['total_samples']
        
        print(f"\n✅ Análisis del modelo real completado!")
        print(f"🎯 Precisión general: {overall_acc:.1%}")
        print(f"📈 Muestras procesadas: {total_samples}")
        
    except Exception as e:
        print(f"❌ Error en análisis del modelo real: {e}")
        import traceback
        traceback.print_exc()


def run_specific_controller(controller_name: str):
    """Ejecutar análisis específico para un controlador"""
    print(f"\n🎯 ANÁLISIS ESPECÍFICO: {controller_name.upper()}")
    print("="*50)
    
    analyzer = GestureConfusionAnalyzer()
    
    if controller_name not in analyzer.controller_gestures:
        print(f"❌ Controlador '{controller_name}' no válido")
        print(f"Disponibles: {', '.join(analyzer.controller_gestures.keys())}")
        return
    
    try:
        # Análisis detallado
        analysis = analyzer.analyze_controller(controller_name, samples_per_gesture=200)
        
        # Generar visualizaciones
        analyzer.visualize_confusion_matrix(controller_name, show_percentages=True)
        analyzer.visualize_confusion_matrix(controller_name, show_percentages=False)
        
        # Generar reporte
        analyzer.generate_detailed_report(controller_name)
        
        # Mostrar resumen
        metrics = analysis['metrics']
        patterns = analysis['confusion_patterns']
        
        print(f"\n📊 RESUMEN - {controller_name.upper()}")
        print(f"🎯 Precisión: {metrics['accuracy']:.1%}")
        print(f"📈 F1-Score: {sum(metrics['f1_per_class'].values())/len(metrics['f1_per_class']):.1%}")
        print(f"📊 Muestras: {analysis['samples_analyzed']:,}")
        
        if patterns['most_confused_pairs']:
            worst = patterns['most_confused_pairs'][0]
            print(f"⚠️ Mayor confusión: {worst['true_gesture']} → {worst['predicted_gesture']} ({worst['confusion_rate']:.1%})")
        
        print(f"\n✅ Análisis de {controller_name} completado!")
        
    except Exception as e:
        print(f"❌ Error analizando {controller_name}: {e}")


def run_interactive_mode():
    """Ejecutar modo interactivo"""
    print("\n🎮 MODO INTERACTIVO")
    print("="*30)
    
    runner = ConfusionAnalysisRunner()
    runner.run()


def show_help():
    """Mostrar ayuda"""
    print("\n📖 AYUDA - ANÁLISIS DE MATRIZ DE CONFUSIÓN")
    print("="*60)
    print("\nComandos disponibles:")
    print("  python quick_start.py demo              - Demo rápido (3 controladores)")
    print("  python quick_start.py full              - Análisis completo sintético")
    print("  python quick_start.py real              - Análisis con modelo real")
    print("  python quick_start.py controller <name> - Análisis específico")
    print("  python quick_start.py interactive       - Modo interactivo")
    print("  python quick_start.py help              - Mostrar esta ayuda")
    print("\nControladores disponibles:")
    analyzer = GestureConfusionAnalyzer()
    for controller, gestures in analyzer.controller_gestures.items():
        print(f"  {controller}: {len(gestures)} gestos")
    print("\nEjemplos:")
    print("  python quick_start.py demo")
    print("  python quick_start.py controller mouse")
    print("  python quick_start.py real")


def show_status():
    """Mostrar estado del sistema"""
    print("\n🔍 ESTADO DEL SISTEMA")
    print("="*35)
    
    # Verificar modelo
    model_path = os.path.join(os.path.dirname(__file__), '../../../../models/gesture_recognizer.task')
    model_exists = os.path.exists(model_path)
    
    print(f"📁 Modelo MediaPipe: {'✅ Disponible' if model_exists else '❌ No encontrado'}")
    if model_exists:
        size_mb = os.path.getsize(model_path) / (1024*1024)
        print(f"   Tamaño: {size_mb:.1f} MB")
    
    # Verificar dependencias
    try:
        import sklearn
        sklearn_ok = True
    except ImportError:
        sklearn_ok = False
    
    try:
        import mediapipe
        mediapipe_ok = True
    except ImportError:
        mediapipe_ok = False
    
    try:
        import matplotlib
        matplotlib_ok = True
    except ImportError:
        matplotlib_ok = False
    
    try:
        import seaborn
        seaborn_ok = True
    except ImportError:
        seaborn_ok = False
    
    print(f"📦 Dependencias:")
    print(f"   scikit-learn: {'✅' if sklearn_ok else '❌'}")
    print(f"   mediapipe: {'✅' if mediapipe_ok else '❌'}")
    print(f"   matplotlib: {'✅' if matplotlib_ok else '❌'}")
    print(f"   seaborn: {'✅' if seaborn_ok else '❌'}")
    
    # Verificar directorios
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    visualizations_dir = os.path.join(reports_dir, 'visualizations')
    data_dir = os.path.join(reports_dir, 'data')
    
    print(f"📂 Directorios:")
    print(f"   reports/: {'✅' if os.path.exists(reports_dir) else '❌'}")
    print(f"   visualizations/: {'✅' if os.path.exists(visualizations_dir) else '❌'}")
    print(f"   data/: {'✅' if os.path.exists(data_dir) else '❌'}")
    
    all_ok = model_exists and sklearn_ok and mediapipe_ok and matplotlib_ok and seaborn_ok
    print(f"\n{'🟢 Sistema listo' if all_ok else '🟡 Verificar dependencias'}")


def main():
    """Función principal"""
    show_banner()
    
    # Configurar argumentos
    parser = argparse.ArgumentParser(description='Análisis de Matriz de Confusión para GestureAI')
    parser.add_argument('command', nargs='?', default='help',
                       choices=['demo', 'full', 'real', 'controller', 'interactive', 'help', 'status'],
                       help='Comando a ejecutar')
    parser.add_argument('controller', nargs='?', 
                       help='Nombre del controlador para análisis específico')
    
    args = parser.parse_args()
    
    # Ejecutar comando
    if args.command == 'demo':
        run_quick_demo()
    
    elif args.command == 'full':
        run_full_synthetic_analysis()
    
    elif args.command == 'real':
        run_real_model_analysis()
    
    elif args.command == 'controller':
        if args.controller:
            run_specific_controller(args.controller)
        else:
            print("❌ Especifica el nombre del controlador")
            print("Ejemplo: python quick_start.py controller mouse")
    
    elif args.command == 'interactive':
        run_interactive_mode()
    
    elif args.command == 'status':
        show_status()
    
    else:  # help
        show_help()
    
    print(f"\n⏰ Completado: {datetime.now().strftime('%H:%M:%S')}")


if __name__ == '__main__':
    main() 