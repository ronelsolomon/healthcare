import sqlite3
from datetime import datetime
import json
from typing import Dict, List, Any

class MarketplaceDB:
    def __init__(self, db_path: str = 'marketplace.db'):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Plans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plans (
                    plan_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    premium REAL,
                    metal_level TEXT,
                    type TEXT,
                    state TEXT,
                    product_division TEXT,
                    insurance_market TEXT,
                    hsa_eligible INTEGER,
                    has_national_network INTEGER,
                    max_age_child INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Issuers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS issuers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT,
                    issuer_id TEXT,
                    name TEXT,
                    state TEXT,
                    toll_free TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
                )
            ''')

            # Benefits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS benefits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT,
                    name TEXT,
                    covered INTEGER,
                    has_limits INTEGER,
                    limit_unit TEXT,
                    limit_quantity INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
                )
            ''')

            # Cost sharings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cost_sharings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT,
                    benefit_name TEXT,
                    network_tier TEXT,
                    copay_amount REAL,
                    coinsurance_rate REAL,
                    display_string TEXT,
                    csr TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
                )
            ''')

            # Deductibles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deductibles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT,
                    type TEXT,
                    amount REAL,
                    network_tier TEXT,
                    family_cost REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
                )
            ''')

            # MOOPs (Maximum Out of Pocket) table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS moops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT,
                    type TEXT,
                    amount REAL,
                    network_tier TEXT,
                    family_cost REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
                )
            ''')

            conn.commit()

    def save_plan_data(self, plan_data: Dict[str, Any]):
        """Save a single plan's data to the database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert or update plan
            cursor.execute('''
                INSERT OR REPLACE INTO plans (
                    plan_id, name, premium, metal_level, type, state,
                    product_division, insurance_market, hsa_eligible,
                    has_national_network, max_age_child
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan_data['id'],
                plan_data.get('name'),
                plan_data.get('premium'),
                plan_data.get('metal_level'),
                plan_data.get('type'),
                plan_data.get('state'),
                plan_data.get('product_division'),
                plan_data.get('insurance_market'),
                int(plan_data.get('hsa_eligible', False)) if 'hsa_eligible' in plan_data else None,
                int(plan_data.get('has_national_network', False)) if 'has_national_network' in plan_data else None,
                plan_data.get('max_age_child')
            ))

            # Save issuer
            if 'issuer' in plan_data and plan_data['issuer']:
                issuer = plan_data['issuer']
                cursor.execute('''
                    INSERT INTO issuers (plan_id, issuer_id, name, state, toll_free)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    plan_data['id'],
                    issuer.get('id'),
                    issuer.get('name'),
                    issuer.get('state'),
                    issuer.get('toll_free')
                ))

            # Save benefits and cost sharings
            for benefit in plan_data.get('benefits', []):
                cursor.execute('''
                    INSERT INTO benefits (
                        plan_id, name, covered, has_limits, limit_unit, limit_quantity
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    plan_data['id'],
                    benefit.get('name'),
                    int(benefit.get('covered', False)) if 'covered' in benefit else None,
                    int(benefit.get('has_limits', False)) if 'has_limits' in benefit else None,
                    benefit.get('limit_unit'),
                    benefit.get('limit_quantity')
                ))

                for sharing in benefit.get('cost_sharings', []):
                    cursor.execute('''
                        INSERT INTO cost_sharings (
                            plan_id, benefit_name, network_tier, copay_amount,
                            coinsurance_rate, display_string, csr
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        plan_data['id'],
                        benefit.get('name'),
                        sharing.get('network_tier'),
                        sharing.get('copay_amount'),
                        sharing.get('coinsurance_rate'),
                        sharing.get('display_string'),
                        sharing.get('csr')
                    ))

            # Save deductibles
            for deductible in plan_data.get('deductibles', []):
                cursor.execute('''
                    INSERT INTO deductibles (
                        plan_id, type, amount, network_tier, family_cost
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    plan_data['id'],
                    deductible.get('type'),
                    deductible.get('amount'),
                    deductible.get('network_tier'),
                    deductible.get('family_cost')
                ))

            # Save MOOPs
            for moop in plan_data.get('moops', []):
                cursor.execute('''
                    INSERT INTO moops (
                        plan_id, type, amount, network_tier, family_cost
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    plan_data['id'],
                    moop.get('type'),
                    moop.get('amount'),
                    moop.get('network_tier'),
                    moop.get('family_cost')
                ))

            conn.commit()

    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """Retrieve a single plan's data from the database"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get plan details
            cursor.execute('SELECT * FROM plans WHERE plan_id = ?', (plan_id,))
            plan = dict(cursor.fetchone()) if cursor.fetchone() else None
            
            if not plan:
                return None
                
            # Get related data
            cursor.execute('SELECT * FROM issuers WHERE plan_id = ?', (plan_id,))
            plan['issuer'] = dict(cursor.fetchone()) if cursor.fetchone() else {}
            
            cursor.execute('SELECT * FROM benefits WHERE plan_id = ?', (plan_id,))
            plan['benefits'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute('SELECT * FROM cost_sharings WHERE plan_id = ?', (plan_id,))
            plan['cost_sharings'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute('SELECT * FROM deductibles WHERE plan_id = ?', (plan_id,))
            plan['deductibles'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute('SELECT * FROM moops WHERE plan_id = ?', (plan_id,))
            plan['moops'] = [dict(row) for row in cursor.fetchall()]
            
            return plan

    def get_all_plans(self) -> List[Dict[str, Any]]:
        """Retrieve all plans from the database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT plan_id FROM plans')
            plan_ids = [row[0] for row in cursor.fetchall()]
            return [self.get_plan(plan_id) for plan_id in plan_ids]

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan and all its related data from the database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM moops WHERE plan_id = ?', (plan_id,))
                cursor.execute('DELETE FROM deductibles WHERE plan_id = ?', (plan_id,))
                cursor.execute('DELETE FROM cost_sharings WHERE plan_id = ?', (plan_id,))
                cursor.execute('DELETE FROM benefits WHERE plan_id = ?', (plan_id,))
                cursor.execute('DELETE FROM issuers WHERE plan_id = ?', (plan_id,))
                cursor.execute('DELETE FROM plans WHERE plan_id = ?', (plan_id,))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.Error:
                conn.rollback()
                return False

def save_marketplace_data(data: dict, db_path: str = 'marketplace.db') -> None:
    """
    Save marketplace data to the SQLite database
    
    Args:
        data: Dictionary containing marketplace data
        db_path: Path to the SQLite database file
    """
    db = MarketplaceDB(db_path)
    
    # Save each plan's data
    for plan_wrapper in data.get('all_plans', []):
        plan = plan_wrapper.get('plan', {})
        if plan:
            db.save_plan_data(plan)
    
    print(f"Successfully saved {len(data.get('all_plans', []))} plans to database")

def export_to_csv(db_path: str = 'marketplace.db', output_dir: str = 'exported_csvs') -> None:
    """
    Export database tables to CSV files
    
    Args:
        db_path: Path to the SQLite database file
        output_dir: Directory to save CSV files
    """
    import os
    import csv
    import sqlite3
    
    os.makedirs(output_dir, exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if not rows:
                continue
                
            # Get column names
            col_names = [description[0] for description in cursor.description]
            
            # Write to CSV
            csv_path = os.path.join(output_dir, f"{table}.csv")
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(col_names)
                writer.writerows(rows)
    
    print(f"Exported {len(tables)} tables to {output_dir}")

if __name__ == "__main__":
    # Example usage
    import json
    
    # Load sample data
    with open('healthcare_plans.json', 'r') as f:
        data = json.load(f)
    
    # Save to database
    save_marketplace_data(data)
    
    # Export to CSV
    export_to_csv()
