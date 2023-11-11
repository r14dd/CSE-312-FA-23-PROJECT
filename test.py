def read_file(file_path):
    with open(file_path, 'r') as file:
        content = file.readlines()
    return content

def create_table(content):
    table = []
    for line in content:
        columns = line.strip().split('|')
        if len(columns) > 1:  # Ensure there are columns in the line
            student_name = columns[1].strip()
            seat_position = columns[2].strip()
            if student_name and seat_position:  # Ensure both values are not empty
                table.append([student_name, seat_position])
    return table

def print_table(table):
    print("{:<15} {:<15}".format('Student Name', 'Seat Position'))
    print("-" * 31)
    for row in table:
        print("{:<15} {:<15}".format(row[0], row[1]))

file_path = 'seating.txt'  # Replace with your file path

content = read_file(file_path)
table = create_table(content)
print_table(table)