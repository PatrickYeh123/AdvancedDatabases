import csv

# Define a function to extract attributes based on boolean values
def extract_attributes(row):
    attributes = []
    if row['Running'] == 'true':
        attributes.append('Running')
    if row['Chasing'] == 'true':
        attributes.append('Chasing')
    if row['Climbing'] == 'true':
        attributes.append('Climbing')
    if row['Eating'] == 'true':
        attributes.append('Eating')
    if row['Foraging'] == 'true':
        attributes.append('Foraging')
    if row['Kuks'] == 'true':
        attributes.append('Kuks')
    if row['Quaas'] == 'true':
        attributes.append('Quaas')
    if row['Moans'] == 'true':
        attributes.append('Moans')
    if row['Tail flags'] == 'true':
        attributes.append('Tail flags')
    if row['Tail twitches'] == 'true':
        attributes.append('Tail twitches')
    if row['Approaches'] == 'true':
        attributes.append('Approaches')
    if row['Indifferent'] == 'true':
        attributes.append('Indifferent')
    if row['Runs from'] == 'true':
        attributes.append('Runs from')
    if row['Other Interactions'] == 'true':
        attributes.append('Other Interactions')
    return attributes

# Open the CSV file
with open('squirrels.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)

    # Create and open the output CSV file
    with open('INTEGRATED-DATASET.csv', 'w', newline='') as output_file:
        writer = csv.writer(output_file)
        # Write the header
        #writer.writerow(['Primary Fur Color', 'Age', 'Hectare', 'Attributes'])

        # Iterate over each row in the input CSV file
        for row in reader:
            # Extract attributes from the row
            attributes = extract_attributes(row)
            # Get other values
            primary_fur_color = row['Primary Fur Color']
            if primary_fur_color != 'Gray':
                primary_fur_color = 'Cinnamon or Black'
            age = row['Age']
            hectare = row['Hectare']
            EW = 'East' if hectare[2] <= 'E' else 'West'
            NS = 'North' if hectare[0] == '0' or int(hectare[:2]) <= 21 else 'South'

            coordinate = NS + " " + EW
            
            shift = row['Shift']
            #endrow = []
            # use the above to isolate for only behaviors, or use the below to add in position/time info
            endrow = [shift, coordinate]
            for attr in attributes:
                endrow.append(attr)
            # Write the extracted attributes along with other values into the output CSV file
            writer.writerow(endrow)

