#!/usr/bin/env python3
"""
BLUE PROTOCOL - PROFIT CALCULATOR (WITH MATHEMATICAL OPTIMIZATION)
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize_scalar

class ProfitCalculator:
    def __init__(self, config_path="config"):
        self.config_path = config_path
        self.daily_focus = 400
        self.load_data()
    
    def load_data(self):
        """Load all data"""
        with open(f"{self.config_path}/market_prices.json") as f:
            self.prices = json.load(f)
        
        with open(f"{self.config_path}/gatherable.json") as f:
            self.gatherable = json.load(f)
        
        with open(f"{self.config_path}/craftable.json") as f:
            self.craftable = json.load(f)
        
        with open(f"{self.config_path}/recipes.json") as f:
            self.recipes = json.load(f)

    def calculate_only_gathering(self):
        """Calculate ONLY direct gathering profits"""
        print("ONLY GATHERING (400 Focus on Ores):")
        print("=" * 70)
        
        results = []
        
        for item, mechanics in self.gatherable.items():
            if item not in self.prices:
                continue
                
            revenue_per_unit = self.prices[item]
            cost_per_unit = 0  # No material costs for gathering
            profit_per_unit = revenue_per_unit - cost_per_unit
            
            Luno_per_focus = (profit_per_unit * mechanics['yield']) / mechanics['focus_cost']
            units_per_day = (self.daily_focus // mechanics['focus_cost']) * mechanics['yield']
            daily_profit = units_per_day * profit_per_unit
            daily_revenue = units_per_day * revenue_per_unit
            
            results.append({
                'method': f"Gather {item}",
                'type': 'only_gathering',
                'revenue_per_unit': revenue_per_unit,
                'cost_per_unit': cost_per_unit,
                'profit_per_unit': profit_per_unit,
                'Luno_per_focus': Luno_per_focus,
                'units_per_day': units_per_day,
                'daily_revenue': daily_revenue,
                'daily_profit': daily_profit
            })
        
        # Sort and display TOP 3 only
        results.sort(key=lambda x: x['Luno_per_focus'], reverse=True)
        top_results = results[:3]
        
        print(f"{'Method':25} | {'Units/Day':>9} | {'Revenue/Unit':>12} | {'Profit/Unit':>11} | {'Luno/Focus':>12} | {'Daily Profit':>12}")
        print("-" * 125)
        
        for r in top_results:
            print(f"{r['method']:25} | {r['units_per_day']:>8,} | {r['revenue_per_unit']:>11,} | {r['profit_per_unit']:>10,} | {r['Luno_per_focus']:>11.1f} | {r['daily_profit']:>11,}")
        
        return results

    def calculate_only_crafting(self):
        """Calculate ONLY crafting profits (buying all materials)"""
        print("\nONLY CRAFTING (400 Focus, Buy Materials):")
        print("=" * 70)
        
        results = []
        
        for product, ingredients in self.recipes.items():
            if product not in self.craftable:
                continue
                
            # Calculate material costs (buying from market)
            total_material_cost = 0
            material_breakdown = []
            for ingredient, quantity in ingredients.items():
                if ingredient in self.prices:
                    cost = self.prices[ingredient] * quantity
                    total_material_cost += cost
                    material_breakdown.append(f"{ingredient}x{quantity}")
            
            # Get crafting mechanics
            mechanics = self.craftable[product]
            revenue_per_unit = self.prices[product]
            cost_per_unit = total_material_cost / mechanics['yield']
            profit_per_unit = revenue_per_unit - cost_per_unit
            
            # Calculate efficiency metrics
            Luno_per_focus = (profit_per_unit * mechanics['yield']) / mechanics['focus_cost']
            units_per_day = (self.daily_focus // mechanics['focus_cost']) * mechanics['yield']
            daily_profit = units_per_day * profit_per_unit
            
            results.append({
                'method': f"Craft {product}",
                'type': 'only_crafting',
                'revenue_per_unit': revenue_per_unit,
                'cost_per_unit': cost_per_unit,
                'profit_per_unit': profit_per_unit,
                'Luno_per_focus': Luno_per_focus,
                'units_per_day': units_per_day,
                'daily_profit': daily_profit,
                'total_material_cost': total_material_cost,
                'materials': ', '.join(material_breakdown)
            })
        
        # Sort and display TOP 3 only
        results.sort(key=lambda x: x['Luno_per_focus'], reverse=True)
        top_results = results[:3]
        
        print(f"{'Method':25} | {'Units/Day':>9} | {'Revenue/Unit':>12} | {'Cost/Unit':>10} | {'Profit/Unit':>11} | {'Luno/Focus':>12} | {'Daily Profit':>12}")
        print("-" * 130)
        
        for r in top_results:
            print(f"{r['method']:25} | {r['units_per_day']:>8,} | {r['revenue_per_unit']:>11,} | {r['cost_per_unit']:>9,} | {r['profit_per_unit']:>10,} | {r['Luno_per_focus']:>11.1f} | {r['daily_profit']:>11,}")
            
            # Show material breakdown for all top 3 items
            print(f"{'':25}   Materials: {r['materials']}")
        
        return results

    def calculate_profit_for_allocation(self, gather_focus, craft_product, gather_item):
        """Calculate profit for a specific focus allocation"""
        craft_focus = self.daily_focus - gather_focus
        
        if gather_focus <= 0 or craft_focus <= 0:
            return -float('inf'), {}
        
        craft_mechanics = self.craftable[craft_product]
        gather_mechanics = self.gatherable[gather_item]
        
        # Calculate material production from gathering
        gather_sessions = gather_focus // gather_mechanics['focus_cost']
        gathered_units = gather_sessions * gather_mechanics['yield']
        
        # Calculate how many crafts we can do
        craft_sessions = craft_focus // craft_mechanics['focus_cost']
        max_possible_crafts = craft_sessions * craft_mechanics['yield']
        
        # Calculate material requirements and costs
        total_material_cost = 0
        material_breakdown = []
        
        for ingredient, quantity in self.recipes[craft_product].items():
            total_needed = quantity * max_possible_crafts
            
            if ingredient == gather_item:
                if gathered_units >= total_needed:
                    bought = 0
                    cost = 0
                else:
                    bought = total_needed - gathered_units
                    cost = bought * self.prices[ingredient]
            else:
                bought = total_needed
                cost = bought * self.prices[ingredient]
            
            total_material_cost += cost
            if bought > 0:
                material_breakdown.append(f"Buy {bought} {ingredient}")
        
        # Calculate profit
        revenue_per_unit = self.prices[craft_product]
        total_revenue = max_possible_crafts * revenue_per_unit
        total_profit = total_revenue - total_material_cost
        
        return total_profit, {
            'gather_focus': gather_focus,
            'craft_focus': craft_focus,
            'gathered_units': gathered_units,
            'crafted_units': max_possible_crafts,
            'material_cost': total_material_cost,
            'material_breakdown': material_breakdown
        }

    def find_optimal_cross_production(self):
        """Find optimal focus allocation using mathematical optimization"""
        print("\nOPTIMAL CROSS-PRODUCTION (Mathematical Optimization):")
        print("=" * 80)
        print("NOTE: Using scipy optimization to find true optimal focus splits")
        print("=" * 80)
        
        results = []
        
        for craft_product, ingredients in self.recipes.items():
            if craft_product not in self.craftable:
                continue
            
            # Try gathering each possible material for this recipe
            for gather_item, gather_mechanics in self.gatherable.items():
                if gather_item not in ingredients:
                    continue
                
                # Define the profit function to optimize
                def profit_function(gather_focus):
                    profit, _ = self.calculate_profit_for_allocation(
                        int(gather_focus), craft_product, gather_item
                    )
                    return -profit  # Negative because we're minimizing
                
                # Method 1: Use scipy's bounded optimization
                try:
                    # Search space: 10 to 390 focus (leaving at least 10 for crafting)
                    result = minimize_scalar(
                        profit_function, 
                        bounds=(10, 390), 
                        method='bounded',
                        options={'xatol': 1}  # 1 focus tolerance
                    )
                    
                    if result.success:
                        optimal_gather_focus = int(result.x)
                        optimal_profit, allocation_details = self.calculate_profit_for_allocation(
                            optimal_gather_focus, craft_product, gather_item
                        )
                        
                        if optimal_profit > 0:
                            # Calculate efficiency
                            total_focus_used = optimal_gather_focus + allocation_details['craft_focus']
                            Luno_per_focus = optimal_profit / total_focus_used
                            
                            results.append({
                                'method': f"Gather {gather_item} + Craft {craft_product}",
                                'type': 'optimal_cross',
                                'gather_item': gather_item,
                                'craft_product': craft_product,
                                'gathered_units': allocation_details['gathered_units'],
                                'crafted_units': allocation_details['crafted_units'],
                                'material_cost': allocation_details['material_cost'],
                                'revenue_per_unit': self.prices[craft_product],
                                'Luno_per_focus': Luno_per_focus,
                                'daily_profit': optimal_profit,
                                'gather_focus_used': optimal_gather_focus,
                                'craft_focus_used': allocation_details['craft_focus'],
                                'material_breakdown': allocation_details['material_breakdown'],
                                'focus_allocation': f"{optimal_gather_focus}G/{allocation_details['craft_focus']}C",
                                'optimization_success': True
                            })
                
                except Exception as e:
                    # Fallback to grid search if optimization fails
                    print(f"Optimization failed for {craft_product} with {gather_item}, using grid search...")
                    
                    # Grid search fallback
                    best_profit = -float('inf')
                    best_allocation = None
                    
                    for gather_focus in range(10, 391, 5):  # Step by 5 for precision
                        profit, allocation_details = self.calculate_profit_for_allocation(
                            gather_focus, craft_product, gather_item
                        )
                        
                        if profit > best_profit:
                            best_profit = profit
                            best_allocation = allocation_details
                            best_allocation['gather_focus'] = gather_focus
                    
                    if best_profit > 0 and best_allocation:
                        total_focus_used = best_allocation['gather_focus'] + best_allocation['craft_focus']
                        Luno_per_focus = best_profit / total_focus_used
                        
                        results.append({
                            'method': f"Gather {gather_item} + Craft {craft_product}",
                            'type': 'optimal_cross',
                            'gather_item': gather_item,
                            'craft_product': craft_product,
                            'gathered_units': best_allocation['gathered_units'],
                            'crafted_units': best_allocation['crafted_units'],
                            'material_cost': best_allocation['material_cost'],
                            'revenue_per_unit': self.prices[craft_product],
                            'Luno_per_focus': Luno_per_focus,
                            'daily_profit': best_profit,
                            'gather_focus_used': best_allocation['gather_focus'],
                            'craft_focus_used': best_allocation['craft_focus'],
                            'material_breakdown': best_allocation['material_breakdown'],
                            'focus_allocation': f"{best_allocation['gather_focus']}G/{best_allocation['craft_focus']}C",
                            'optimization_success': False
                        })
        
        # Sort by efficiency and take TOP 3 only
        results.sort(key=lambda x: x['Luno_per_focus'], reverse=True)
        top_results = results[:3]
        
        # Display results
        print(f"{'Method':40} | {'Focus Split':>11} | {'Gather Units':>12} | {'Craft Units':>10} | {'Buy Cost':>9} | {'Luno/Focus':>12} | {'Daily Profit':>12}")
        print("-" * 130)
        
        for r in top_results:
            print(f"{r['method']:40} | {r['focus_allocation']:>10} | {r['gathered_units']:>11,} | {r['crafted_units']:>9,} | {r['material_cost']:>8,} | {r['Luno_per_focus']:>11.1f} | {r['daily_profit']:>11,}")
            
            # Show detailed breakdown for all top 3
            print(f"{'':40}   Materials: {', '.join(r['material_breakdown'])}")
            print(f"{'':40}   → Optimal: {r['gather_focus_used']} focus gathering, {r['craft_focus_used']} focus crafting")
        
        return results

    def analyze_sensitivity(self):
        """Analyze how sensitive profits are to focus allocation changes"""
        print("\nSENSITIVITY ANALYSIS:")
        print("=" * 80)
        print("NOTE: How much profit changes with ±20 focus allocation")
        print("=" * 80)
        
        sensitivity_results = []
        
        for craft_product, ingredients in self.recipes.items():
            if craft_product not in self.craftable:
                continue
            
            for gather_item in self.gatherable.keys():
                if gather_item not in ingredients:
                    continue
                
                # Find optimal allocation using brute force
                best_profit = -float('inf')
                best_gather_focus = 0
                
                for gather_focus in range(10, 391, 10):
                    profit, _ = self.calculate_profit_for_allocation(gather_focus, craft_product, gather_item)
                    if profit > best_profit:
                        best_profit = profit
                        best_gather_focus = gather_focus
                
                if best_profit > 0:
                    # Test sensitivity: ±20 focus
                    profit_plus_20, _ = self.calculate_profit_for_allocation(
                        min(390, best_gather_focus + 20), craft_product, gather_item
                    )
                    profit_minus_20, _ = self.calculate_profit_for_allocation(
                        max(10, best_gather_focus - 20), craft_product, gather_item
                    )
                    
                    max_change = max(
                        abs(profit_plus_20 - best_profit),
                        abs(profit_minus_20 - best_profit)
                    )
                    sensitivity_percent = (max_change / best_profit) * 100 if best_profit > 0 else 100
                    
                    sensitivity_results.append({
                        'method': f"Gather {gather_item} + Craft {craft_product}",
                        'optimal_focus': best_gather_focus,
                        'optimal_profit': best_profit,
                        'sensitivity_percent': sensitivity_percent,
                        'robustness': 'High' if sensitivity_percent < 5 else 'Medium' if sensitivity_percent < 15 else 'Low'
                    })
        
        # Display sensitivity analysis - TOP 3 only
        sensitivity_results.sort(key=lambda x: x['sensitivity_percent'])
        top_results = sensitivity_results[:3]
        
        print(f"{'Method':40} | {'Optimal Focus':>13} | {'Optimal Profit':>14} | {'Sensitivity':>12} | {'Robustness':>10}")
        print("-" * 110)
        
        for r in top_results:
            print(f"{r['method']:40} | {r['optimal_focus']:>12}G | {r['optimal_profit']:>13,} | {r['sensitivity_percent']:>11.1f}% | {r['robustness']:>9}")
        
        return sensitivity_results

    def show_comparison(self, gathering_results, crafting_results, cross_results, sensitivity_results=None):
        """Compare all methods with optimization insights - TOP 10 only"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE COMPARISON WITH OPTIMIZATION")
        print("=" * 80)
        
        all_results = []
        
        # Add all result types
        for r in gathering_results:
            all_results.append({
                'method': r['method'],
                'type': 'Only Gathering',
                'daily_profit': r['daily_profit'],
                'Luno_per_focus': r['Luno_per_focus'],
                'units_per_day': r['units_per_day'],
                'focus_info': '400G'
            })
        
        for r in crafting_results:
            all_results.append({
                'method': r['method'],
                'type': 'Only Crafting',
                'daily_profit': r['daily_profit'],
                'Luno_per_focus': r['Luno_per_focus'],
                'units_per_day': r['units_per_day'],
                'focus_info': '400C'
            })
        
        for r in cross_results:
            all_results.append({
                'method': r['method'],
                'type': 'Optimal Cross',
                'daily_profit': r['daily_profit'],
                'Luno_per_focus': r['Luno_per_focus'],
                'units_per_day': r['crafted_units'],
                'focus_info': r.get('focus_allocation', 'N/A')
            })
        
        # Display comparison table - TOP 10 only
        print(f"{'Method':45} | {'Type':15} | {'Focus':>8} | {'Units/Day':>10} | {'Luno/Focus':>12} | {'Daily Profit':>12}")
        print("-" * 120)
        
        for r in sorted(all_results, key=lambda x: x['daily_profit'], reverse=True)[:10]:
            print(f"{r['method']:45} | {r['type']:15} | {r['focus_info']:>7} | {r['units_per_day']:>9,} | {r['Luno_per_focus']:>11.1f} | {r['daily_profit']:>11,}")
        
        # Show optimization insights
        if sensitivity_results:
            print(f"\n{'OPTIMIZATION INSIGHTS:':50}")
            robust_methods = [r for r in sensitivity_results if r['robustness'] == 'High']
            if robust_methods:
                best_robust = robust_methods[0]
                print(f"{'Most robust method:':50} {best_robust['method']}")
                print(f"{'Sensitivity to allocation changes:':50} {best_robust['sensitivity_percent']:.1f}%")
                print(f"{'Recommendation:':50} High robustness to focus allocation errors")
        
        return all_results

    def get_final_recommendation(self, comparison_results, sensitivity_results=None):
        """Get the final best recommendation"""
        print("\n" + "=" * 50)
        print("FINAL RECOMMENDATION")
        print("=" * 50)
        
        if not comparison_results:
            print("No data available for recommendation")
            return
        
        # Find absolute best method
        best_overall = max(comparison_results, key=lambda x: x['daily_profit'])
        
        print(f"🏆 BEST OVERALL: {best_overall['method']}")
        print(f"   Daily Profit: {best_overall['daily_profit']:,} Luno")
        print(f"   Efficiency: {best_overall['Luno_per_focus']:.1f} Luno/Focus")
        print(f"   Type: {best_overall['type']}")
        
        # Find best robust method
        best_robust = None
        if sensitivity_results:
            robust_methods = [r for r in sensitivity_results if r['robustness'] == 'High']
            if robust_methods:
                best_robust = robust_methods[0]
                # Find this method in comparison results
                for result in comparison_results:
                    if result['method'] == best_robust['method']:
                        best_robust_result = result
                        break
        
        if best_robust and best_robust_result['daily_profit'] > best_overall['daily_profit'] * 0.95:
            print(f"\n🛡️  BEST ROBUST: {best_robust['method']}")
            print(f"   Daily Profit: {best_robust_result['daily_profit']:,} Luno ({(best_robust_result['daily_profit']/best_overall['daily_profit']*100):.1f}% of best)")
            print(f"   Sensitivity: {best_robust['sensitivity_percent']:.1f}% (Very forgiving)")
            print(f"   Recommendation: Choose this for consistent results")
        
        print(f"\n💡 STRATEGY ANALYSIS:")
        if best_overall['type'] == 'Only Gathering':
            print("   • Focus on gathering high-value ores directly")
            print("   • No material costs, simple to execute")
        elif best_overall['type'] == 'Only Crafting':
            print("   • Buy all materials from market and focus on crafting")
            print("   • Higher risk (market prices), but potentially higher reward")
        elif best_overall['type'] == 'Optimal Cross':
            print("   • Split focus between gathering and crafting")
            print("   • Balance between self-sufficiency and market dependency")

# EXECUTE
if __name__ == "__main__":
    calculator = ProfitCalculator()
    
    print("BLUE PROTOCOL - OPTIMIZED PROFIT ANALYSIS")
    print("=" * 50)
    
    # Run all analyses
    gathering_results = calculator.calculate_only_gathering()
    crafting_results = calculator.calculate_only_crafting()
    cross_results = calculator.find_optimal_cross_production()
    sensitivity_results = calculator.analyze_sensitivity()
    
    # Compare all methods
    comparison_results = calculator.show_comparison(
        gathering_results, crafting_results, cross_results, sensitivity_results
    )
    
    # Final recommendation
    calculator.get_final_recommendation(comparison_results, sensitivity_results)
    
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE!")
    print("=" * 50)