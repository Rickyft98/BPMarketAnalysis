#!/usr/bin/env python3
"""
BLUE PROTOCOL - PROFIT CALCULATOR (OPTIMIZED)
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize_scalar

class ProfitCalculatorOptimized:
    def __init__(self, config_path="config", daily_focus=400):
        self.config_path = config_path
        self.daily_focus = daily_focus
        self.prices = {}
        self.gatherable = {}
        self.craftable = {}
        self.recipes = {}
        self.load_data()

    def load_data(self):
        """Load all data"""
        try:
            with open(f"{self.config_path}/market_prices.json") as f:
                self.prices = json.load(f)

            with open(f"{self.config_path}/gatherable.json") as f:
                self.gatherable = json.load(f)

            with open(f"{self.config_path}/craftable.json") as f:
                self.craftable = json.load(f)

            with open(f"{self.config_path}/recipes.json") as f:
                self.recipes = json.load(f)
        except FileNotFoundError as e:
            print(f"Error loading data file: {e}")
            print("Please ensure the 'config' directory and its JSON files are in the correct location.")
            raise e

    def get_material_requirements(self, craft_product, quantity):
        """Calculate exact material requirements for crafting"""
        requirements = {}
        if craft_product in self.recipes:
            for ingredient, amount in self.recipes[craft_product].items():
                requirements[ingredient] = amount * quantity
        return requirements

    def calculate_profit_buy_all(self, craft_product):
        """Calculate profit when buying ALL materials (optimal baseline)"""
        if craft_product not in self.craftable or craft_product not in self.prices:
            return -float('inf'), {}
            
        craft_mechanics = self.craftable[craft_product]
        if craft_mechanics['focus_cost'] <= 0:
            return -float('inf'), {}
            
        # Maximum crafting with all focus
        max_crafts = (self.daily_focus // craft_mechanics['focus_cost']) * craft_mechanics['yield']
        
        # Calculate material costs (buying everything)
        total_material_cost = 0
        material_breakdown_list = []
        materials_found = True
        
        for ingredient, quantity in self.recipes[craft_product].items():
            if ingredient in self.prices:
                total_needed = quantity * max_crafts
                cost = total_needed * self.prices[ingredient]
                total_material_cost += cost
                material_breakdown_list.append(f"Buy {total_needed} {ingredient}")
            else:
                materials_found = False
                break
                
        if not materials_found:
            return -float('inf'), {}
            
        # Calculate profit
        revenue_per_unit = self.prices[craft_product]
        total_revenue = max_crafts * revenue_per_unit
        total_profit = total_revenue - total_material_cost
        
        return total_profit, {
            'method': 'buy_all',
            'crafted_units': max_crafts,
            'material_cost': total_material_cost,
            'material_breakdown': ', '.join(material_breakdown_list),
            'craft_focus_used': self.daily_focus,
            'gather_focus_used': 0
        }

    def calculate_only_gathering(self):
        """Calculate ONLY direct gathering profits and return as DataFrame"""
        results = []
        for item, mechanics in self.gatherable.items():
            if item in self.prices and mechanics['focus_cost'] > 0:
                revenue_per_unit = self.prices[item]
                profit_per_unit = revenue_per_unit # Cost is 0
                luno_per_focus = (profit_per_unit * mechanics['yield']) / mechanics['focus_cost']
                units_per_day = (self.daily_focus // mechanics['focus_cost']) * mechanics['yield']
                daily_profit = units_per_day * profit_per_unit

                results.append({
                    'Method': f"Gather {item}",
                    'Type': 'Only Gathering',
                    'Units/Day': units_per_day,
                    'Revenue/Unit': revenue_per_unit,
                    'Cost/Unit': 0,
                    'Profit/Unit': profit_per_unit,
                    'Luno/Focus': luno_per_focus,
                    'Daily Profit': daily_profit
                })
            elif item not in self.prices:
                 print(f"Warning: Price for {item} not found. Skipping gathering analysis for this item.")


        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values(by='Luno/Focus', ascending=False)
        return df

    def calculate_profit_for_allocation(self, gather_focus, craft_product, gather_item):
        """Calculate profit for a specific focus allocation - CORREGIDO"""
        craft_focus = self.daily_focus - gather_focus

        if gather_focus < 0 or craft_focus < 0:
             return -float('inf'), {} # Invalid allocation

        gather_mechanics = self.gatherable.get(gather_item)
        craft_mechanics = self.craftable.get(craft_product)

        if not gather_mechanics or not craft_mechanics:
             return -float('inf'), {}

        # Ensure focus is allocated in multiples of the cost
        if gather_mechanics['focus_cost'] > 0:
            gather_focus = (gather_focus // gather_mechanics['focus_cost']) * gather_mechanics['focus_cost']
        if craft_mechanics['focus_cost'] > 0:
            craft_focus = (craft_focus // craft_mechanics['focus_cost']) * craft_mechanics['focus_cost']

        # Recalculate to ensure total is self.daily_focus
        craft_focus = self.daily_focus - gather_focus

        if gather_focus < 0 or craft_focus < 0:
            return -float('inf'), {}

        # Calculate material production from gathering
        if gather_mechanics['focus_cost'] > 0:
            gather_sessions = gather_focus // gather_mechanics['focus_cost']
            gathered_units = gather_sessions * gather_mechanics['yield']
        else:
            gather_sessions = 0
            gathered_units = 0

        # Calculate how many crafts we can do
        if craft_mechanics['focus_cost'] > 0:
            craft_sessions = craft_focus // craft_mechanics['focus_cost']
            max_possible_crafts = craft_sessions * craft_mechanics['yield']
        else:
            craft_sessions = 0
            max_possible_crafts = 0

        # Calculate material requirements and costs
        total_material_cost = 0
        material_breakdown_list = []
        materials_available = True

        ingredients = self.recipes.get(craft_product, {})
        if not ingredients:
             return -float('inf'), {}

        for ingredient, quantity in ingredients.items():
            if ingredient not in self.prices:
                materials_available = False
                break

            total_needed = quantity * max_possible_crafts

            if ingredient == gather_item:
                bought = max(0, total_needed - gathered_units)
            else:
                bought = total_needed

            cost = bought * self.prices.get(ingredient, 0)
            total_material_cost += cost

            if bought > 0:
                material_breakdown_list.append(f"Buy {bought} {ingredient}")

        if not materials_available:
            return -float('inf'), {}

        # Calculate profit
        revenue_per_unit = self.prices.get(craft_product, 0)
        total_revenue = max_possible_crafts * revenue_per_unit
        total_profit = total_revenue - total_material_cost

        # ✅ CORRECCIÓN: Compare with "buy all" strategy
        profit_buy_all, _ = self.calculate_profit_buy_all(craft_product)
        
        # If buying all is better, return that instead
        if profit_buy_all > total_profit:
            return profit_buy_all, {
                'method': 'buy_all_better',
                'original_profit': total_profit,
                'improvement': profit_buy_all - total_profit
            }

        return total_profit, {
            'gather_focus': gather_focus,
            'craft_focus': craft_focus,
            'gathered_units': gathered_units,
            'crafted_units': max_possible_crafts,
            'material_cost': total_material_cost,
            'material_breakdown': ', '.join(material_breakdown_list),
            'method': 'mixed'
        }

    def find_optimal_strategies(self):
        """Find truly optimal strategies without duplicates"""
        results = []

        for craft_product, ingredients in self.recipes.items():
            if craft_product not in self.craftable:
                continue

            # Calculate profit for buying all (baseline)
            profit_buy_all, buy_all_details = self.calculate_profit_buy_all(craft_product)
            if profit_buy_all <= 0:
                continue

            best_profit = profit_buy_all
            best_method = f"Craft {craft_product}"
            best_type = "Optimal Strategy"
            best_allocation = "0G/400C"
            best_focus_allocation = "0G/400C"
            optimization_method = "Buy All"
            material_details = buy_all_details

            # Check if mixed strategy is better
            for gather_item, gather_mechanics in self.gatherable.items():
                if gather_item not in ingredients:
                    continue

                # Check if prices exist for all necessary items
                if craft_product not in self.prices or gather_item not in self.prices:
                    continue
                    
                materials_found = True
                for ingredient in ingredients:
                    if ingredient not in self.prices:
                        materials_found = False
                        break
                if not materials_found:
                    continue

                gather_mech = self.gatherable[gather_item]
                craft_mech = self.craftable[craft_product]

                if gather_mech['focus_cost'] <= 0 or craft_mech['focus_cost'] <= 0:
                    continue

                # Define the profit function to optimize
                def profit_function(gather_focus):
                    profit, _ = self.calculate_profit_for_allocation(
                        int(gather_focus), craft_product, gather_item
                    )
                    return -profit  # Negative because we're minimizing

                # Use scipy's bounded optimization
                try:
                    min_gather_focus = gather_mech['focus_cost']
                    min_craft_focus = craft_mech['focus_cost']
                    upper_bound = self.daily_focus - min_craft_focus
                    lower_bound = min_gather_focus

                    if upper_bound < lower_bound:
                        continue

                    result = minimize_scalar(
                        profit_function,
                        bounds=(lower_bound, upper_bound),
                        method='bounded',
                        options={'xatol': 1}
                    )

                    if result.success:
                        optimal_gather_focus = int(result.x)
                        optimal_gather_focus = (optimal_gather_focus // gather_mech['focus_cost']) * gather_mech['focus_cost']
                        optimal_craft_focus = self.daily_focus - optimal_gather_focus
                        
                        optimal_profit, allocation_details = self.calculate_profit_for_allocation(
                            optimal_gather_focus, craft_product, gather_item
                        )

                        if optimal_profit > best_profit:
                            best_profit = optimal_profit
                            best_method = f"Gather {gather_item} + Craft {craft_product}"
                            best_type = "Optimal Cross"
                            best_allocation = f"{optimal_gather_focus}G/{optimal_craft_focus}C"
                            best_focus_allocation = f"{optimal_gather_focus}G/{optimal_craft_focus}C"
                            optimization_method = "Mixed"
                            material_details = allocation_details

                except Exception as e:
                    continue

            # Add only the BEST strategy (no duplicates)
            material_requirements = self.get_material_requirements(craft_product, material_details['crafted_units'])
            materials_needed = ", ".join([f"{qty} {mat}" for mat, qty in material_requirements.items()])
            
            # Calculate material breakdown for display
            if optimization_method == "Mixed" and 'gathered_units' in material_details:
                gathered_amount = material_details['gathered_units']
                total_needed = material_requirements.get(gather_item, 0)
                buy_amount = max(0, total_needed - gathered_amount)
                
                other_materials = []
                for material, quantity in material_requirements.items():
                    if material != gather_item:
                        other_materials.append(f"{quantity} {material}")
                
                you_gather = f"{gathered_amount} {gather_item}"
                you_buy = f"{buy_amount} {gather_item}" if buy_amount > 0 else "None"
                other_mats = ", ".join(other_materials) if other_materials else "None"
            else:
                you_gather = "None"
                you_buy = materials_needed
                other_mats = "None"

            results.append({
                'Method': best_method,
                'Type': best_type,
                'Crafted Units': material_details['crafted_units'],
                'Daily Profit': best_profit,
                'Luno/Focus': best_profit / self.daily_focus,
                'Focus Allocation': best_focus_allocation,
                'Total Materials Needed': materials_needed,
                'You Will Gather': you_gather,
                'You Need To Buy': you_buy,
                'Other Materials Needed': other_mats,
                'Optimization Method': optimization_method
            })

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values(by='Daily Profit', ascending=False)
        
        return df

    def calculate_sensitivity(self, optimal_result, focus_change=20):
        """Calculate sensitivity for a given optimal result"""
        method = optimal_result.get('Method', '')
        optimal_profit = optimal_result.get('Daily Profit', 0)

        if optimal_profit <= 0:
            return 0, "N/A"

        # For "buy all" strategies, sensitivity is typically low
        if "Gather" not in method:
            return 1.0, "High"  # Buying all is very stable

        # For mixed strategies, calculate basic sensitivity
        craft_product = None
        for product in self.recipes:
            if product in method:
                craft_product = product
                break

        if not craft_product:
            return 0, "N/A"

        profit_buy_all, _ = self.calculate_profit_buy_all(craft_product)
        
        if optimal_profit > 0:
            sensitivity = abs(optimal_profit - profit_buy_all) / optimal_profit * 100
        else:
            sensitivity = float('inf')

        if sensitivity < 5:
            robustness = "High"
        elif sensitivity < 15:
            robustness = "Medium"
        else:
            robustness = "Low"

        return sensitivity, robustness

    def run_analysis(self):
        """Run the full profit analysis and return results as a dictionary of DataFrames"""
        try:
            results = {}

            # 1. ONLY GATHERING
            results['gathering'] = self.calculate_only_gathering()

            # 2. OPTIMAL STRATEGIES (sin duplicados)
            results['optimal_strategies'] = self.find_optimal_strategies()

            # 3. COMPREHENSIVE COMPARISON (combinar gathering + optimal strategies)
            comparison_cols = ['Method', 'Type', 'Daily Profit', 'Luno/Focus']
            comprehensive_dfs = []

            # Add gathering strategies
            if not results['gathering'].empty:
                gathering_compare = results['gathering'][comparison_cols].copy()
                comprehensive_dfs.append(gathering_compare)

            # Add optimal strategies
            if not results['optimal_strategies'].empty:
                optimal_compare = results['optimal_strategies'][comparison_cols].copy()
                comprehensive_dfs.append(optimal_compare)

            # Combine and remove duplicates
            if comprehensive_dfs:
                comprehensive_df = pd.concat(comprehensive_dfs, ignore_index=True)
                # Remove exact duplicates based on key metrics
                comprehensive_df = comprehensive_df.drop_duplicates(subset=['Method', 'Daily Profit', 'Luno/Focus'])
                results['comprehensive'] = comprehensive_df.sort_values(by='Daily Profit', ascending=False)
            else:
                results['comprehensive'] = pd.DataFrame(columns=comparison_cols)

            # Calculate sensitivity for optimal strategies
            if not results['optimal_strategies'].empty:
                results['optimal_strategies'][['Sensitivity', 'Robustness']] = results['optimal_strategies'].apply(
                    lambda row: self.calculate_sensitivity(row),
                    axis=1,
                    result_type='expand'
                )

            return results

        except Exception as e:
            print(f"An error occurred during analysis: {e}")
            import traceback
            traceback.print_exc()
            return {}
    def get_available_products(self):
        """Return list of available product names"""
        return [p for p in self.recipes.keys() if p in self.craftable]
    
    def show_available_products(self):
        """Show all available craftable products"""
        available_products = self.get_available_products()
        print("\n📦 AVAILABLE PRODUCTS:")
        print("-" * 30)
        for i, product in enumerate(available_products, 1):
            print(f"{i}. {product}")
        print(f"\nTotal: {len(available_products)} craftable products")

    def analyze_single_product(self, product_name):
        """Analyze a single specific product"""
        if product_name not in self.recipes:
            print(f"❌ Product '{product_name}' not found!")
            return None
    
        if product_name not in self.craftable:
            print(f"❌ Crafting mechanics for '{product_name}' not found!")
            return None

        print(f"\n🔍 Analyzing: {product_name}")
        print("=" * 50)
    
        # Calculate profit for buying all
        profit_buy_all, details = self.calculate_profit_buy_all(product_name)
    
        if profit_buy_all <= 0:
            print(f"❌ {product_name} is not profitable")
            return None
    
        # Show basic info
        print(f"💰 Daily Profit (Buy All): {profit_buy_all:,} Luno")
        print(f"⚡ Efficiency: {profit_buy_all / self.daily_focus:.1f} Luno/Focus")
        print(f"🛠️ Crafts per day: {details['crafted_units']}")
        print(f"📦 Materials needed: {details['material_breakdown']}")
    
        # Check if mixed strategy is better
        best_profit = profit_buy_all
        best_strategy = "Buy All Materials"
    
        for gather_item, gather_mech in self.gatherable.items():
            if gather_item in self.recipes[product_name]:
                # Quick test with minimal gathering
                test_profit, test_details = self.calculate_profit_for_allocation(
                    gather_mech['focus_cost'], product_name, gather_item
                )
            
                if test_profit > best_profit:
                    best_profit = test_profit
                    best_strategy = f"Gather {gather_item} + Craft"
    
        print(f"🎯 Best Strategy: {best_strategy}")
        return {
            'product': product_name,
            'daily_profit': best_profit,
            'efficiency': best_profit / self.daily_focus,
            'strategy': best_strategy
        }


# Main execution block
if __name__ == "__main__":
    # Instantiate the OPTIMIZED calculator
    calculator = ProfitCalculatorOptimized()
    
    # Run the analysis
    print("🔄 Running OPTIMIZED profit analysis...")
    results = calculator.run_analysis()
    
    # Print results to console
    print("\n" + "="*60)
    print("PROFIT ANALYSIS RESULTS (OPTIMIZED):")
    print("="*60)
    
    for key, df in results.items():
        if not df.empty:
            print(f"\n{key.upper().replace('_', ' ')}:")
            print("-" * 40)
            
            if key == 'optimal_strategies':
                # Show ALL optimal strategies (no limit)
                important_cols = ['Method', 'Crafted Units', 'Daily Profit', 'Luno/Focus', 
                                'Focus Allocation', 'Total Materials Needed', 'You Will Gather', 
                                'You Need To Buy', 'Other Materials Needed', 'Optimization Method']
                available_cols = [col for col in important_cols if col in df.columns]
                print(df[available_cols].to_string(index=False))
            
            elif key == 'comprehensive':
                # Show TOP 10 comprehensive results
                print("TOP 10 STRATEGIES:")
                print(df.head(10).to_string(index=False))
                
                # Show additional stats
                print(f"\n📊 Total strategies analyzed: {len(df)}")
                if len(df) > 10:
                    print("💡 Showing top 10 by Daily Profit")
            
            else:
                # Show all gathering results
                print(df.to_string(index=False))
            print()