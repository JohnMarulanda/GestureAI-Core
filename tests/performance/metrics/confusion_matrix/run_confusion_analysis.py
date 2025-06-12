#!/usr/bin/env python3
"""
Runner Interactivo para Análisis de Matriz de Confusión
Ejecuta análisis detallado de clasificación de gestos
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from gesture_confusion_analyzer import GestureConfusionAnalyzer


class ConfusionAnalysisRunner:
    """Runner para análisis de matriz de confusión"""
    
    def __init__(self):
        """Inicializar el runner"""
        self.analyzer = GestureConfusionAnalyzer()
        self.results = {}
        self.session_log = []  # Para guardar todos los resultados y mensajes
        
    def log_result(self, message: str, data: Any = None):
        """Guardar resultado o mensaje en el log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'data': data
        }
        self.session_log.append(log_entry)
        print(message)

    def generate_readme(self) -> str:
        """
        Generar README con todos los resultados del análisis
        
        Returns:
            str: Ruta al archivo README generado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        readme_content = []
        
        # Encabezado
        readme_content.append("# 📊 Reporte de Análisis de Matriz de Confusión")
        readme_content.append(f"\nGenerado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        readme_content.append("\n## 📋 Resumen de la Sesión")
        
        # Estadísticas generales
        total_controllers = len(self.results)
        if total_controllers > 0:
            total_samples = sum(a.get('samples_analyzed', 0) for a in self.results.values())
            avg_accuracy = sum(a.get('metrics', {}).get('accuracy', 0) for a in self.results.values()) / total_controllers
            
            readme_content.append(f"\n### 📈 Estadísticas Generales")
            readme_content.append(f"- Controladores analizados: {total_controllers}")
            readme_content.append(f"- Total de muestras: {total_samples:,}")
            readme_content.append(f"- Precisión promedio: {avg_accuracy:.1%}")
        
        # Resultados por controlador
        if self.results:
            readme_content.append("\n## 🎯 Resultados por Controlador")
            
            for controller, analysis in self.results.items():
                readme_content.append(f"\n### {controller.upper()}")
                
                if 'metrics' in analysis:
                    metrics = analysis['metrics']
                    readme_content.append(f"- Precisión: {metrics['accuracy']:.1%}")
                    readme_content.append(f"- Muestras analizadas: {analysis['samples_analyzed']:,}")
                    
                    # F1-Score promedio
                    if 'f1_per_class' in metrics:
                        avg_f1 = sum(metrics['f1_per_class'].values()) / len(metrics['f1_per_class'])
                        readme_content.append(f"- F1-Score promedio: {avg_f1:.1%}")
                
                # Patrones de confusión
                if 'confusion_patterns' in analysis:
                    patterns = analysis['confusion_patterns']
                    
                    if patterns.get('most_confused_pairs'):
                        readme_content.append("\n#### 🔄 Principales Confusiones:")
                        for pair in patterns['most_confused_pairs'][:3]:
                            readme_content.append(f"- {pair['true_gesture']} → {pair['predicted_gesture']}: {pair['confusion_rate']:.1%}")
                    
                    if patterns.get('best_recognized_gestures'):
                        readme_content.append("\n#### ✅ Gestos Mejor Reconocidos:")
                        for gesture in patterns['best_recognized_gestures'][:3]:
                            readme_content.append(f"- {gesture['gesture']}: {gesture['accuracy']:.1%}")
        
        # Log completo de la sesión
        readme_content.append("\n## 📝 Log Completo de la Sesión")
        for entry in self.session_log:
            readme_content.append(f"\n### {entry['timestamp']}")
            readme_content.append(f"{entry['message']}")
            
            if entry['data'] and isinstance(entry['data'], dict):
                # Formatear datos JSON de manera legible
                readme_content.append("\n```json")
                readme_content.append(json.dumps(entry['data'], indent=2, ensure_ascii=False))
                readme_content.append("```")
        
        # Rutas a archivos generados
        readme_content.append("\n## 📁 Archivos Generados")
        readme_content.append("\n### Visualizaciones")
        vis_dir = os.path.join(os.path.dirname(__file__), 'reports', 'visualizations')
        if os.path.exists(vis_dir):
            for file in os.listdir(vis_dir):
                if file.endswith('.png'):
                    readme_content.append(f"- [{file}](reports/visualizations/{file})")
        
        readme_content.append("\n### Reportes")
        reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
        if os.path.exists(reports_dir):
            for file in os.listdir(reports_dir):
                if file.endswith('.txt'):
                    readme_content.append(f"- [{file}](reports/{file})")
        
        # Guardar README
        readme_path = os.path.join(os.path.dirname(__file__), 'reports', f'README_{timestamp}.md')
        os.makedirs(os.path.dirname(readme_path), exist_ok=True)
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(readme_content))
        
        return readme_path
        
    def show_welcome(self):
        """Mostrar mensaje de bienvenida"""
        welcome_msg = "\n" + "="*80 + "\n"
        welcome_msg += "🧠 GESTUREAI - ANÁLISIS DE MATRIZ DE CONFUSIÓN 🧠\n"
        welcome_msg += "="*80 + "\n"
        welcome_msg += "Análisis detallado de clasificación de gestos con visualizaciones\n"
        welcome_msg += f"Modelo utilizado: {os.path.basename(self.analyzer.model_path)}\n"
        welcome_msg += "="*80
        
        self.log_result(welcome_msg)
    
    def show_menu(self):
        """Mostrar menú de opciones"""
        menu_msg = "\n📋 OPCIONES DE ANÁLISIS:\n"
        menu_msg += "─" * 50 + "\n"
        menu_msg += "1. 🔍 Análisis rápido (Top 3 controladores)\n"
        menu_msg += "2. 📊 Análisis completo (todos los controladores)\n"
        menu_msg += "3. 🎯 Análisis específico por controlador\n"
        menu_msg += "4. 📈 Comparativa entre controladores\n"
        menu_msg += "5. 🔄 Análisis de patrones de confusión\n"
        menu_msg += "6. 📝 Generar reporte ejecutivo\n"
        menu_msg += "7. ❌ Salir\n"
        menu_msg += "─" * 50
        
        self.log_result(menu_msg)
    
    def run_quick_analysis(self):
        """Ejecutar análisis rápido de top controladores"""
        self.log_result("\n🚀 ANÁLISIS RÁPIDO - TOP 3 CONTROLADORES")
        self.log_result("="*60)
        
        # Controladores prioritarios
        priority_controllers = ['mouse', 'shortcuts', 'volume']
        
        start_time = time.time()
        
        for i, controller in enumerate(priority_controllers, 1):
            self.log_result(f"\n[{i}/3] Analizando {controller.upper()}...")
            
            try:
                # Análisis con menos muestras para rapidez
                analysis = self.analyzer.analyze_controller(controller, samples_per_gesture=100)
                
                # Generar visualización
                self.analyzer.visualize_confusion_matrix(controller)
                
                # Mostrar métricas clave
                metrics = analysis['metrics']
                patterns = analysis['confusion_patterns']
                
                result_msg = f"   ✅ Precisión: {metrics['accuracy']:.1%}\n"
                result_msg += f"   📈 F1-Score: {sum(metrics['f1_per_class'].values())/len(metrics['f1_per_class']):.1%}"
                
                if patterns['most_confused_pairs']:
                    worst_confusion = patterns['most_confused_pairs'][0]
                    result_msg += f"\n   ⚠️  Mayor confusión: {worst_confusion['true_gesture']} → {worst_confusion['predicted_gesture']} ({worst_confusion['confusion_rate']:.1%})"
                
                self.log_result(result_msg, analysis)
                self.results[controller] = analysis
                
            except Exception as e:
                self.log_result(f"   ❌ Error: {e}")
        
        elapsed = time.time() - start_time
        self.log_result(f"\n⏱️  Análisis completado en {elapsed:.1f} segundos")
        
        # Resumen rápido
        self._show_quick_summary()
        
        # Generar README con resultados
        readme_path = self.generate_readme()
        self.log_result(f"\n📝 README generado: {readme_path}")
    
    def run_full_analysis(self):
        """Ejecutar análisis completo de todos los controladores"""
        print("\n🔍 ANÁLISIS COMPLETO - TODOS LOS CONTROLADORES")
        print("="*70)
        
        start_time = time.time()
        
        try:
            results = self.analyzer.analyze_all_controllers()
            self.results.update(results['individual_analyses'])
            
            elapsed = time.time() - start_time
            print(f"\n⏱️  Análisis completo en {elapsed:.1f} segundos")
            
            # Mostrar análisis comparativo
            self._show_comparative_analysis(results['comparative_analysis'])
            
            # Guardar resultados
            self._save_comprehensive_results(results)
            
        except Exception as e:
            print(f"❌ Error en análisis completo: {e}")
    
    def run_specific_analysis(self):
        """Ejecutar análisis específico por controlador"""
        print("\n🎯 ANÁLISIS ESPECÍFICO POR CONTROLADOR")
        print("="*50)
        
        # Mostrar controladores disponibles
        controllers = list(self.analyzer.controller_gestures.keys())
        print("\nControladores disponibles:")
        for i, controller in enumerate(controllers, 1):
            gestures = self.analyzer.controller_gestures[controller]
            print(f"{i}. {controller.upper()} ({len(gestures)} gestos)")
        
        # Selección del usuario
        try:
            choice = input("\nSelecciona controlador (1-7): ").strip()
            controller_idx = int(choice) - 1
            
            if 0 <= controller_idx < len(controllers):
                controller = controllers[controller_idx]
                
                print(f"\n🔍 Analizando {controller.upper()} en detalle...")
                
                # Análisis detallado con más muestras
                analysis = self.analyzer.analyze_controller(controller, samples_per_gesture=200)
                
                # Generar visualizaciones
                self.analyzer.visualize_confusion_matrix(controller, show_percentages=True)
                self.analyzer.visualize_confusion_matrix(controller, show_percentages=False)
                
                # Generar reporte detallado
                report_path = self.analyzer.generate_detailed_report(controller)
                
                # Mostrar análisis detallado
                self._show_detailed_analysis(analysis)
                
                self.results[controller] = analysis
                
            else:
                print("❌ Selección inválida")
                
        except (ValueError, KeyboardInterrupt):
            print("❌ Operación cancelada")
    
    def run_comparative_analysis(self):
        """Ejecutar análisis comparativo entre controladores"""
        print("\n📈 ANÁLISIS COMPARATIVO ENTRE CONTROLADORES")
        print("="*60)
        
        if len(self.results) < 2:
            print("⚠️  Se necesitan al menos 2 controladores analizados")
            print("   Ejecuta primero análisis individual o completo")
            return
        
        # Ranking de precisión
        print("\n🏆 RANKING DE PRECISIÓN:")
        print("─" * 40)
        
        ranking = []
        for controller, analysis in self.results.items():
            accuracy = analysis['metrics']['accuracy']
            ranking.append((controller, accuracy))
        
        ranking.sort(key=lambda x: x[1], reverse=True)
        
        for i, (controller, accuracy) in enumerate(ranking, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
            print(f"{emoji} {i}. {controller.upper()}: {accuracy:.1%}")
        
        # Análisis de gestos comunes
        self._analyze_common_gestures()
        
        # Patrones de confusión globales
        self._analyze_global_confusion_patterns()
    
    def run_pattern_analysis(self):
        """Analizar patrones específicos de confusión"""
        print("\n🔄 ANÁLISIS DE PATRONES DE CONFUSIÓN")
        print("="*50)
        
        if not self.results:
            print("⚠️  No hay resultados disponibles")
            print("   Ejecuta primero un análisis")
            return
        
        # Patrones globales
        all_confusions = []
        gesture_difficulties = {}
        
        for controller, analysis in self.results.items():
            patterns = analysis['confusion_patterns']
            
            # Recopilar confusiones
            for pair in patterns['most_confused_pairs']:
                all_confusions.append({
                    'controller': controller,
                    'true_gesture': pair['true_gesture'],
                    'predicted_gesture': pair['predicted_gesture'],
                    'confusion_rate': pair['confusion_rate']
                })
            
            # Recopilar dificultades
            for gesture, difficulty in patterns['classification_difficulty'].items():
                if gesture not in gesture_difficulties:
                    gesture_difficulties[gesture] = []
                gesture_difficulties[gesture].append({
                    'controller': controller,
                    'accuracy': difficulty['accuracy'],
                    'difficulty_score': difficulty['difficulty_score']
                })
        
        # Mostrar patrones más problemáticos
        print("\n🚨 PATRONES PROBLEMÁTICOS GLOBALES:")
        print("─" * 45)
        
        all_confusions.sort(key=lambda x: x['confusion_rate'], reverse=True)
        for i, confusion in enumerate(all_confusions[:5], 1):
            print(f"{i}. {confusion['controller'].upper()}: "
                  f"{confusion['true_gesture']} → {confusion['predicted_gesture']} "
                  f"({confusion['confusion_rate']:.1%})")
        
        # Mostrar gestos más difíciles
        print("\n😰 GESTOS MÁS DIFÍCILES DE RECONOCER:")
        print("─" * 40)
        
        avg_difficulties = {}
        for gesture, difficulties in gesture_difficulties.items():
            avg_diff = sum(d['difficulty_score'] for d in difficulties) / len(difficulties)
            avg_difficulties[gesture] = avg_diff
        
        sorted_difficulties = sorted(avg_difficulties.items(), key=lambda x: x[1], reverse=True)
        for i, (gesture, difficulty) in enumerate(sorted_difficulties[:5], 1):
            accuracy = 1 - difficulty
            print(f"{i}. {gesture}: {accuracy:.1%} precisión promedio")
    
    def generate_executive_report(self):
        """Generar reporte ejecutivo"""
        print("\n📝 GENERANDO REPORTE EJECUTIVO")
        print("="*40)
        
        if not self.results:
            print("⚠️  No hay resultados para reportar")
            return
        
        # Crear reporte ejecutivo
        report = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report.append("# REPORTE EJECUTIVO - MATRIZ DE CONFUSIÓN")
        report.append(f"Generado: {timestamp}")
        report.append("=" * 60)
        
        # Resumen general
        total_samples = sum(a['samples_analyzed'] for a in self.results.values())
        avg_accuracy = sum(a['metrics']['accuracy'] for a in self.results.values()) / len(self.results)
        
        report.append(f"\n## 📊 RESUMEN EJECUTIVO")
        report.append(f"Controladores analizados: {len(self.results)}")
        report.append(f"Muestras totales procesadas: {total_samples:,}")
        report.append(f"Precisión promedio: {avg_accuracy:.1%}")
        
        # Ranking de rendimiento
        ranking = sorted(self.results.items(), key=lambda x: x[1]['metrics']['accuracy'], reverse=True)
        
        report.append(f"\n## 🏆 RANKING DE RENDIMIENTO")
        for i, (controller, analysis) in enumerate(ranking, 1):
            accuracy = analysis['metrics']['accuracy']
            status = "🟢" if accuracy >= 0.90 else "🟡" if accuracy >= 0.80 else "🔴"
            report.append(f"{i}. {controller.upper()}: {accuracy:.1%} {status}")
        
        # Recomendaciones
        report.append(f"\n## 💡 RECOMENDACIONES CLAVE")
        
        # Controladores con baja precisión
        low_accuracy = [c for c, a in self.results.items() if a['metrics']['accuracy'] < 0.85]
        if low_accuracy:
            report.append(f"• Priorizar mejoras en: {', '.join(low_accuracy)}")
        
        # Gestos problemáticos
        problematic_gestures = set()
        for analysis in self.results.values():
            for gesture in analysis['confusion_patterns']['worst_recognized_gestures']:
                if gesture['accuracy'] < 0.80:
                    problematic_gestures.add(gesture['gesture'])
        
        if problematic_gestures:
            report.append(f"• Revisar entrenamiento para gestos: {', '.join(problematic_gestures)}")
        
        # Patrones de confusión críticos
        critical_confusions = []
        for analysis in self.results.values():
            for pair in analysis['confusion_patterns']['most_confused_pairs']:
                if pair['confusion_rate'] > 0.15:  # >15% confusión es crítico
                    critical_confusions.append(f"{pair['true_gesture']}→{pair['predicted_gesture']}")
        
        if critical_confusions:
            report.append(f"• Atender confusiones críticas: {', '.join(set(critical_confusions))}")
        
        # Guardar reporte
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = os.path.join(os.path.dirname(__file__), 'reports')
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f'executive_report_{timestamp_file}.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"📝 Reporte ejecutivo guardado: {report_path}")
        
        # Mostrar resumen en pantalla
        print("\n📋 RESUMEN EJECUTIVO:")
        print("─" * 30)
        print(f"🎯 Precisión promedio: {avg_accuracy:.1%}")
        print(f"📊 Controladores analizados: {len(self.results)}")
        print(f"📈 Mejor rendimiento: {ranking[0][0].upper()} ({ranking[0][1]['metrics']['accuracy']:.1%})")
        
        if len(ranking) > 1:
            print(f"📉 Necesita mejora: {ranking[-1][0].upper()} ({ranking[-1][1]['metrics']['accuracy']:.1%})")
    
    def _show_quick_summary(self):
        """Mostrar resumen rápido"""
        if not self.results:
            return
        
        print("\n📋 RESUMEN RÁPIDO:")
        print("─" * 40)
        
        for controller, analysis in self.results.items():
            accuracy = analysis['metrics']['accuracy']
            status = "✅" if accuracy >= 0.90 else "⚠️" if accuracy >= 0.80 else "❌"
            print(f"{status} {controller.upper()}: {accuracy:.1%}")
    
    def _show_comparative_analysis(self, comparative: Dict[str, Any]):
        """Mostrar análisis comparativo"""
        print("\n📊 ANÁLISIS COMPARATIVO:")
        print("─" * 50)
        
        # Ranking de precisión
        print("\n🏆 Ranking por precisión:")
        for i, item in enumerate(comparative['accuracy_ranking'][:5], 1):
            controller = item['controller']
            accuracy = item['accuracy']
            print(f"  {i}. {controller.upper()}: {accuracy:.1%}")
        
        # Gestos más difíciles globalmente
        print("\n😰 Gestos más desafiantes:")
        gesture_diff = comparative['gesture_difficulty_across_controllers']
        sorted_gestures = sorted(gesture_diff.items(), key=lambda x: x[1]['average_accuracy'])
        
        for gesture, stats in sorted_gestures[:3]:
            avg_acc = stats['average_accuracy']
            controllers_count = stats['controllers_using']
            print(f"  • {gesture}: {avg_acc:.1%} (usado en {controllers_count} controladores)")
    
    def _show_detailed_analysis(self, analysis: Dict[str, Any]):
        """Mostrar análisis detallado de un controlador"""
        controller = analysis['controller']
        metrics = analysis['metrics']
        patterns = analysis['confusion_patterns']
        
        print(f"\n📊 ANÁLISIS DETALLADO - {controller.upper()}")
        print("─" * 50)
        
        # Métricas generales
        print(f"🎯 Precisión general: {metrics['accuracy']:.1%}")
        print(f"📈 F1-Score promedio: {sum(metrics['f1_per_class'].values())/len(metrics['f1_per_class']):.1%}")
        print(f"📊 Muestras analizadas: {analysis['samples_analyzed']:,}")
        
        # Mejores y peores gestos
        print(f"\n✅ Gestos mejor reconocidos:")
        for gesture in patterns['best_recognized_gestures']:
            print(f"   • {gesture['gesture']}: {gesture['accuracy']:.1%}")
        
        print(f"\n⚠️ Gestos con dificultades:")
        for gesture in patterns['worst_recognized_gestures']:
            print(f"   • {gesture['gesture']}: {gesture['accuracy']:.1%}")
        
        # Confusiones principales
        if patterns['most_confused_pairs']:
            print(f"\n🔄 Principales confusiones:")
            for pair in patterns['most_confused_pairs'][:3]:
                print(f"   • {pair['true_gesture']} → {pair['predicted_gesture']}: {pair['confusion_rate']:.1%}")
    
    def _analyze_common_gestures(self):
        """Analizar gestos comunes entre controladores"""
        print("\n🤝 ANÁLISIS DE GESTOS COMUNES:")
        print("─" * 35)
        
        # Encontrar gestos usados en múltiples controladores
        gesture_usage = {}
        for controller, analysis in self.results.items():
            for gesture in analysis['labels']:
                if gesture not in gesture_usage:
                    gesture_usage[gesture] = []
                gesture_usage[gesture].append(controller)
        
        # Mostrar gestos comunes y su rendimiento
        common_gestures = {g: controllers for g, controllers in gesture_usage.items() if len(controllers) > 1}
        
        for gesture, controllers in common_gestures.items():
            accuracies = []
            for controller in controllers:
                if controller in self.results:
                    acc = self.results[controller]['metrics']['precision_per_class'].get(gesture, 0)
                    accuracies.append(acc)
            
            if accuracies:
                avg_acc = sum(accuracies) / len(accuracies)
                min_acc = min(accuracies)
                max_acc = max(accuracies)
                print(f"• {gesture}: {avg_acc:.1%} promedio (rango: {min_acc:.1%}-{max_acc:.1%})")
    
    def _analyze_global_confusion_patterns(self):
        """Analizar patrones de confusión globales"""
        print("\n🌍 PATRONES GLOBALES DE CONFUSIÓN:")
        print("─" * 40)
        
        # Recopilar todas las confusiones
        all_pairs = {}
        
        for analysis in self.results.values():
            for pair in analysis['confusion_patterns']['most_confused_pairs']:
                key = f"{pair['true_gesture']} → {pair['predicted_gesture']}"
                if key not in all_pairs:
                    all_pairs[key] = []
                all_pairs[key].append(pair['confusion_rate'])
        
        # Encontrar patrones consistentes
        consistent_patterns = {}
        for pair, rates in all_pairs.items():
            if len(rates) > 1:  # Aparece en múltiples controladores
                avg_rate = sum(rates) / len(rates)
                consistent_patterns[pair] = avg_rate
        
        # Mostrar patrones más problemáticos
        sorted_patterns = sorted(consistent_patterns.items(), key=lambda x: x[1], reverse=True)
        
        for i, (pair, avg_rate) in enumerate(sorted_patterns[:5], 1):
            print(f"{i}. {pair}: {avg_rate:.1%} promedio")
    
    def _save_comprehensive_results(self, results: Dict[str, Any]):
        """Guardar resultados completos en JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_dir = os.path.join(os.path.dirname(__file__), 'reports', 'data')
        os.makedirs(results_dir, exist_ok=True)
        
        # Preparar datos para JSON (convertir numpy arrays)
        json_results = self._prepare_for_json(results)
        
        results_path = os.path.join(results_dir, f'confusion_analysis_{timestamp}.json')
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultados guardados: {results_path}")
    
    def _prepare_for_json(self, data):
        """Preparar datos para serialización JSON"""
        import numpy as np
        
        if isinstance(data, dict):
            return {k: self._prepare_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        else:
            return data
    
    def run(self):
        """Ejecutar el runner interactivo"""
        self.show_welcome()
        
        while True:
            try:
                self.show_menu()
                choice = input("\nSelecciona una opción (1-7): ").strip()
                
                if choice == '1':
                    self.run_quick_analysis()
                elif choice == '2':
                    self.run_full_analysis()
                elif choice == '3':
                    self.run_specific_analysis()
                elif choice == '4':
                    self.run_comparative_analysis()
                elif choice == '5':
                    self.run_pattern_analysis()
                elif choice == '6':
                    self.generate_executive_report()
                elif choice == '7':
                    self.log_result("\n👋 ¡Hasta luego!")
                    # Generar README final
                    readme_path = self.generate_readme()
                    self.log_result(f"\n📝 README final generado: {readme_path}")
                    break
                else:
                    self.log_result("❌ Opción inválida. Selecciona 1-7.")
                
                input("\n⏸️  Presiona Enter para continuar...")
                
            except KeyboardInterrupt:
                self.log_result("\n\n👋 ¡Hasta luego!")
                # Generar README final
                readme_path = self.generate_readme()
                self.log_result(f"\n📝 README final generado: {readme_path}")
                break
            except Exception as e:
                self.log_result(f"\n❌ Error inesperado: {e}")
                input("⏸️  Presiona Enter para continuar...")


def main():
    """Función principal"""
    runner = ConfusionAnalysisRunner()
    runner.run()


if __name__ == '__main__':
    main()