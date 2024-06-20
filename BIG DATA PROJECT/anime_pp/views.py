import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from io import StringIO
from collections import Counter
from django.shortcuts import redirect


def index(request):
    # Initialize variable to hold book data, column statistics, and flag for file selection
    book_data = None  
    column_stats = None  
    file_selected = False  
    max_rows = 100    

    # Check if the request method is POST
    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            
            # Check if the uploaded file is a CSV file
            if not csv_file.name.endswith('.csv'):
                return HttpResponse('File is not a CSV')

            # Use pandas to read the CSV file
            try:
                df = pd.read_csv(csv_file)

                # Add a row number column to the DataFrame
                df.insert(0, 'Number', range(1, len(df) + 1))

                # Store the uploaded file contents in the session
                request.session['uploaded_file_contents'] = df.to_csv(index=False)

                # Now you have a DataFrame 'df' containing your CSV data
                # You can pass this data to the template for rendering
                book_data = df.head(max_rows).to_dict(orient='records')

                # Calculate mean, median, mode, standard deviation, range, max, min, and total rows for each numeric column
                numeric_columns = df.select_dtypes(include='number').columns
                column_stats = {}
                for column in numeric_columns:
                    if 'id' not in column.lower() and column != 'Number':  # Check if the column is not 'id' or 'RowNumber'
                        column_stats[column] = {
                            'mean': float(df[column].mean()),
                            'median': float(df[column].median()),
                            'mode': float(df[column].mode().values[0]),
                            'std': float(df[column].std()),
                            'min': float(df[column].min()),
                            'max': float(df[column].max()),
                            'range': float(df[column].max() - df[column].min()),
                            'total_rows': int(len(df))
                        }

                # Save column stats to the session
                request.session['column_stats'] = column_stats

                file_selected = True  # Set flag to True as file was selected and processed

            except pd.errors.ParserError as e:
                return HttpResponse(f'Error parsing CSV file: {e}')
    else:
        # If no new file is uploaded, retrieve the previously uploaded file from the session
        if 'uploaded_file_contents' in request.session:
            csv_data = StringIO(request.session['uploaded_file_contents'])
            df = pd.read_csv(csv_data)

            # Add a row number column to the DataFrame
            # df.insert(0, 'Number', range(1, len(df) + 1))

            book_data = df.head(max_rows).to_dict(orient='records')
            file_selected = True

            # Retrieve column stats from session if available
            column_stats = request.session.get('column_stats')

    # Render the template with the data
    return render(request, 'index.html', {'book_data': book_data, 'file_selected': file_selected, 'column_stats': column_stats})


    # Render the template with the data
    return render(request, 'index.html', {'book_data': book_data, 'file_selected': file_selected, 'column_stats': column_stats})
def clean_data(request):
    if request.method == 'POST':
        # Retrieve the uploaded file contents from the session
        uploaded_file_contents = request.session.get('uploaded_file_contents')

        if not uploaded_file_contents:
            return HttpResponse('No file uploaded')

        # Read the uploaded file into a pandas DataFrame
        try:
            csv_data = StringIO(uploaded_file_contents)
            df = pd.read_csv(csv_data)

            # Replace "Unknown" with NaN
            df.replace('Unknown', pd.NA, inplace=True)

            # Drop rows with any null values
            cleaned_data = df.dropna(how='any')

            # Convert the cleaned DataFrame to a CSV file
            cleaned_csv = cleaned_data.to_csv(index=False)

            # Save cleaned file contents to the session
            request.session['cleaned_file_contents'] = cleaned_csv

            # Redirect to another view where the system will use the cleaned data
            return redirect('process_cleaned_data')  # Assuming there's a URL named 'process_cleaned_data'

        except Exception as e:
            return HttpResponse(f'Error cleaning CSV file: {e}')

    return HttpResponse('No file uploaded') 


def statistics(request):
    # Retrieve column statistics from the session
    column_stats = request.session.get('column_stats')

    # Check if column_stats is None, handle the case where no file was uploaded
    if column_stats is None:
        return HttpResponse("No statistics available. Please upload a CSV file first.")

    return render(request, 'stats.html', {'column_stats': column_stats})


def insights(request):
    # Get CSV data from session
    csv_data = request.session.get('uploaded_file_contents')
    if not csv_data:
        return HttpResponse("No data available. Please upload a CSV file first.")

    # Read the CSV data into a DataFrame
    df = pd.read_csv(StringIO(csv_data))

    # Words to remove from text data
    words_to_remove = ['to', 'the']

    # Filter out rows containing 'Unknown'
    df = df[~df.apply(lambda row: row.astype(str).str.lower().str.contains('unknown').any(), axis=1)]

    # Columns to exclude from insights
    exclude_columns = ['Name']
    # exclude_columns += [f'Score-{i}' for i in range(1, 11)]  # Uncomment if you need to exclude Score-1 to Score-10

    # Initialize a dictionary to hold insights for each column
    insights = {}

    for column in df.columns:
        if column not in exclude_columns:
            column_insights = {}
            if not pd.api.types.is_numeric_dtype(df[column]) and df[column].dtype == object:
                # Non-numeric column insights for words
                words = ' '.join(df[column].astype(str)).split()  # Join all strings in the column, split by space
                words_without_specific_words = [word for word in words if word.lower() not in words_to_remove]  # Remove specified words
                word_counts = Counter(words_without_specific_words)
                most_common_words = word_counts.most_common(10)  # Get the top 5 most common words
                # Filter out specific words if they appear in the most common words
                most_common_words = [(word, count) for word, count in most_common_words if word.lower() not in words_to_remove]
                column_insights['top use'] = most_common_words

            # Add insights for the current column to the main dictionary
            insights[column] = column_insights

    # Render the template with the insights
    return render(request, 'insights.html', {'insights': insights})



def top(request):
    csv_data = request.session.get('uploaded_file_contents')
    if not csv_data:
        return HttpResponse("No data available. Please upload a CSV file first.")

    # Read the CSV data into a DataFrame
    df = pd.read_csv(StringIO(csv_data))



    # Convert 'NA_Sales' column to numeric type
    df['NA_Sales'] = pd.to_numeric(df['NA_Sales'], errors='coerce')

    # Sort the DataFrame based on 'NA_Sales' to get top 10 NA Sales
    df_sorted_na_sales = df.sort_values(by='NA_Sales', ascending=False)
    top_10_na_sales_data = df_sorted_na_sales.head(10).to_dict(orient='records')



    # Convert 'JP_Sales' column to numeric type
    df['JP_Sales'] = pd.to_numeric(df['JP_Sales'], errors='coerce')

    # Sort the DataFrame based on 'JP_Sales' to get top 10 JP Sales
    df_sorted_jp_sales = df.sort_values(by='JP_Sales', ascending=False)
    top_10_jp_sales_data = df_sorted_jp_sales.head(10).to_dict(orient='records')


    # Convert 'EU_Sales' column to numeric type
    df['EU_Sales'] = pd.to_numeric(df['EU_Sales'], errors='coerce')

    # Sort the DataFrame based on 'EU_Sales' to get top 10 JP Sales
    df_sorted_eu_sales = df.sort_values(by='EU_Sales', ascending=False)
    top_10_eu_sales_data = df_sorted_eu_sales.head(10).to_dict(orient='records')



    # Convert 'Other_Sales' column to numeric type
    df['Other_Sales'] = pd.to_numeric(df['Other_Sales'], errors='coerce')

    # Sort the DataFrame based on 'EU_Sales' to get top 10 EU Sales
    df_sorted_Other_sales = df.sort_values(by='Other_Sales', ascending=False)
    top_10_Other_sales_data = df_sorted_Other_sales.head(10).to_dict(orient='records')


    # Convert 'Global_Sales' column to numeric type
    df['Global_Sales'] = pd.to_numeric(df['Global_Sales'], errors='coerce')

    # Sort the DataFrame based on 'Global_Sales' to get top 10 Global Sales
    df_sorted_Global_sales = df.sort_values(by='Global_Sales', ascending=False)
    top_10_Global_sales_data = df_sorted_Global_sales.head(10).to_dict(orient='records')


    # Convert 'Critic_Score' column to numeric type
    df['Critic_Score'] = pd.to_numeric(df['Critic_Score'], errors='coerce')

    # Sort the DataFrame based on 'Critic_Score' to get top 10 Critic Score
    df_sorted_Critic_Score = df.sort_values(by='Critic_Score', ascending=False)
    top_10_Critic_Score_data = df_sorted_Critic_Score.head(10).to_dict(orient='records')


    # Convert 'Critic_Score' column to numeric type
    df['Critic_Count'] = pd.to_numeric(df['Critic_Count'], errors='coerce')

    # Sort the DataFrame based on 'Critic_Score' to get top 10 Critic Score
    df_sorted_Critic_Count = df.sort_values(by='Critic_Count', ascending=False)
    top_10_Critic_Count_data = df_sorted_Critic_Count.head(10).to_dict(orient='records')

    
    # Convert 'Critic_Score' column to numeric type
    df['User_Score'] = pd.to_numeric(df['User_Score'], errors='coerce')

    # Sort the DataFrame based on 'Critic_Score' to get top 10 Critic Score
    df_sorted_User_Score = df.sort_values(by='User_Score', ascending=False)
    top_10_User_Score_data = df_sorted_User_Score.head(10).to_dict(orient='records')


    # Convert 'Critic_Score' column to numeric type
    df['User_Count'] = pd.to_numeric(df['User_Count'], errors='coerce')

    # Sort the DataFrame based on 'Critic_Score' to get top 10 Critic Score
    df_sorted_User_Count = df.sort_values(by='User_Count', ascending=False)
    top_10_User_Count_data = df_sorted_User_Count.head(10).to_dict(orient='records')


    # Define the columns to consider for ranking based on total score
    ranking_columns = ['NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales', 'Global_Sales', 'Critic_Score', 'Critic_Count', 'User_Score', 'User_Count']

    # Convert all numeric columns to numeric type
    df[ranking_columns] = df[ranking_columns].apply(pd.to_numeric, errors='coerce')

    # Calculate total score for each row by summing all selected numeric columns
    df['total_score'] = df[ranking_columns].sum(axis=1)

    # Rank the rows based on total score to get top 10 rows
    top_10_rows = df.nlargest(10, 'total_score')
    top_10_rows_data = top_10_rows.to_dict(orient='records')
    first_row_keys = list(top_10_rows_data[0].keys()) if top_10_rows_data else []




    # Render the template with the top 10 NA Sales, top 10 JP Sales, and top 10 rows based on total score
    return render(request, 'top.html', {'top_10_na_sales_data': top_10_na_sales_data, 'top_10_eu_sales_data': top_10_eu_sales_data, 'top_10_jp_sales_data': top_10_jp_sales_data, 'top_10_Other_sales_data': top_10_Other_sales_data, 'top_10_Critic_Score_data': top_10_Critic_Score_data, 'top_10_Critic_Count_data': top_10_Critic_Count_data, 'top_10_Global_sales_data': top_10_Global_sales_data, 'top_10_User_Score_data': top_10_User_Score_data, 'top_10_User_Count_data': top_10_User_Count_data, 'top_10_rows_data': top_10_rows_data, 'first_row_keys': first_row_keys})





def visualize(request):
    return render(request,'visual.html')

def about(request):
    return render(request,'about.html')