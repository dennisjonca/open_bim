# IFC Query Tool - Usage Guide

## Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/dennisjonca/open_bim.git
cd open_bim
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

**Development Mode:**
```bash
python app.py
```

**Production Mode:**
```bash
# Set environment variables
export SECRET_KEY="your-secure-random-key-here"
export FLASK_DEBUG="false"

# Use a production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Using the Web Interface

### Step 1: Upload an IFC File

1. On the home page, click "Choose IFC File"
2. Select your IFC file (must have .ifc or .IFC extension)
3. Click "Upload File"
4. Wait for validation - you'll be redirected to the query interface

### Step 2: Select a Query Category

The interface provides 9 query categories:

1. **Quantity & Cost Estimation** - Count elements per floor or total
2. **Lengths & Volumes** - Calculate material quantities
3. **Element Context** - Find elements in specific locations
4. **System Analysis** - Analyze MEP systems and circuits
5. **Space & Usage** - Analyze room areas and usage
6. **Compliance** - Check if elements are in required locations
7. **Planning** - Identify high-density areas for installation
8. **Maintenance** - Locate devices requiring maintenance
9. **Compound Queries** - Complex multi-filter queries

### Step 3: Configure Your Query

Each category has specific query options. For example:

**Quantity & Cost Estimation:**
- Select element type (outlets, doors, windows, etc.)
- Choose between "by storey" or "total" count

**Compound Queries:**
- Select element type
- Optionally filter by storey (e.g., "First Floor")
- Optionally filter by space type (e.g., "Office")

### Step 4: Execute and View Results

1. Fill in the query parameters
2. Click "Execute Query"
3. Results appear below in one of three formats:
   - **Value**: Single numeric result with units
   - **Table**: Multiple rows of data
   - **Compliance**: Pass/fail status with details

## Example Queries

### Example 1: Count Outlets per Floor

1. Go to "Quantity & Cost Estimation"
2. Select query: "Count by Storey"
3. Element Type: "Electrical Outlets"
4. Click "Execute Query"

**Result:** Table showing count of outlets on each floor

### Example 2: Total Pipe Length

1. Go to "Lengths & Volumes"
2. Select query: "Total Length"
3. Element Type: "Piping"
4. Click "Execute Query"

**Result:** Total length in meters

### Example 3: Outlets in Office Spaces

1. Go to "Element Context"
2. Select query: "Elements in Space Type"
3. Element Type: "Outlets"
4. Space Type: "Office"
5. Click "Execute Query"

**Result:** Count of outlets in office spaces

### Example 4: Check Compliance

1. Go to "Compliance"
2. Select query: "Check Elements in All Spaces"
3. Element Type: "Outlets"
4. Space Type: "Office"
5. Click "Execute Query"

**Result:** Shows if all office spaces have outlets

### Example 5: Compound Query

1. Go to "Compound Queries"
2. Select query: "Filtered Element Count"
3. Element Type: "Outlets"
4. Storey Filter: "First"
5. Space Type Filter: "Office"
6. Click "Execute Query"

**Result:** Count of outlets in office spaces on the first floor

## Understanding Results

### Value Results
Shows a single number with units:
```
Total Electrical Outlets: 156 items
```

### Table Results
Shows multiple rows:
```
Storey              | Count
--------------------|-------
Ground Floor        | 45
First Floor         | 52
Second Floor        | 38
```

### Compliance Results
Shows pass/fail status:
```
✓ All spaces have elements
Total Office spaces: 25
Spaces with Outlets: 25
Spaces missing Outlets: 0
```

## Tips and Best Practices

### Query Performance
- Start with simple queries to understand your data
- Use filters to narrow down results
- Some queries may take time with large IFC files

### Data Quality
The quality of results depends on your IFC file:
- **Element Classification**: Elements should be properly classified (not all proxies)
- **Storey Assignment**: Elements should be assigned to floors
- **System Data**: MEP elements should be assigned to systems for system queries
- **Spatial Relationships**: Elements should be contained in or referenced by spaces

### Troubleshooting

**Query returns no data:**
- Check if elements of that type exist in your IFC file
- Check if elements are properly assigned to storeys/spaces
- Try the "Elements per Floor" query to see what's available

**Elements showing as "Unassigned":**
- Elements may not be assigned to a floor in your BIM model
- Check spatial relationships in your BIM authoring tool

**System queries return empty:**
- MEP elements may not be assigned to systems in your model
- Use your BIM authoring tool to create and assign systems

## Command Line Alternative

For batch processing or scripting, use the original analyzer:
```bash
# Place IFC file in the same directory
python analyze_ifc.py
```

This provides detailed console output with all available data.

## Security Notes

### For Production Deployment

1. **Always set a secure SECRET_KEY:**
```bash
export SECRET_KEY="$(python -c 'import os; print(os.urandom(24).hex())')"
```

2. **Disable debug mode:**
```bash
export FLASK_DEBUG="false"
```

3. **Use a production WSGI server** (not Flask's built-in server):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

4. **Set up proper file permissions** for the uploads directory

5. **Consider adding authentication** if deploying publicly

6. **Set up HTTPS** with a reverse proxy (nginx, Apache)

7. **Limit file upload sizes** (already set to 100MB)

## Support

For issues or questions:
- Check the README.md for general information
- Review the original analyze_ifc.py for detailed IFC analysis
- Consult ifcopenshell documentation for IFC schema details
