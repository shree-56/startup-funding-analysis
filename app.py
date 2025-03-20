import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
st.set_page_config(layout='wide',page_title='StartUp Data Analysis')

df = pd.read_csv('startup_data_cleaned.csv')
investors_list = sorted(set(df['investors'].str.split(',').sum()))
investors_list = [i.strip().lower() for i in investors_list]
for i in investors_list:
    if '&' in i:
        investors_list.remove(i)
        investors_list.extend(i.split(' & '))
    elif 'and' in i:
        investors_list.remove(i)
        investors_list.extend(i.split(' and '))
investors_list=sorted(set(investors_list))
df['date'] = pd.to_datetime(df['date'],errors='coerce')
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year
st.sidebar.title('Startup Funding Analysis')
st.session_state.option = st.sidebar.selectbox('Select One',['Overall Analysis','StartUp','Investor'])
option = st.session_state.option

def load_overall_analysis():
    st.title('Overall Analysis')

    # total invested amount
    total = round(df['amount (Cr)'].sum())
    # max amount infused in a startup
    max_funding = df.groupby('startup')['amount (Cr)'].max().sort_values(ascending=False).head(1).values[0]
    # avg ticket size
    avg_funding = df.groupby('startup')['amount (Cr)'].sum().mean()
    # total funded startups
    num_startups = df['startup'].nunique()

    col1,col2,col3,col4 = st.columns(4)

    with col1:
        st.metric('Total',str(total) + ' Cr')
    with col2:
        st.metric('Max', str(max_funding) + ' Cr')

    with col3:
        st.metric('Avg',str(round(avg_funding)) + ' Cr')

    with col4:
        st.metric('Funded Startups',num_startups)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('MoM graph')
        selected_option = st.selectbox('Select Type',['Total','Count'])
        if selected_option == 'Total':
            temp_df = df.groupby(['year', 'month'])['amount (Cr)'].sum().reset_index()
        else:
            temp_df = df.groupby(['year', 'month'])['amount (Cr)'].count().reset_index()
        temp_df['m-yyyy'] = temp_df['month'].astype('str') + '-' + temp_df['year'].astype('str')
        line_chart = px.line(temp_df, x='m-yyyy', y='amount (Cr)')
        st.plotly_chart(line_chart)
    with col2:
        #year wise analysis - finding the top startups and investors in each year
        st.subheader('Hall of Fame')
        df_empty = pd.DataFrame()
        selected_option = st.selectbox('Select Type',['Top Startups','Top Investors'])
        if selected_option == 'Top Startups':
            def year_wise_analysis(year):
                temp = df[df['year']==year].groupby('startup').agg({'amount (Cr)':['sum','count']}).\
                sort_values(by = [('amount (Cr)','sum'),('amount (Cr)','count')], ascending=False).head(1).reset_index()
                temp.insert(0,'year',year)
                return temp  
        else:
            def year_wise_analysis(year):
                d = {}
                temp = df[df['year'] == year]
                for index, row in temp.iterrows():
                    t1 = str(row['investors']).split(',')
                    t = [i.strip() for i in t1]
                    for i in t:
                        if i not in d:
                            d[i] = [row['amount (Cr)'],1]
                        else:
                            d[i][0] += row['amount (Cr)']
                            d[i][1] += 1              
                temp = pd.DataFrame({'investors':list(d.keys()),
                                    'amount (Cr) sum':[ i[0] for i in list(d.values())],
                                    'amount (Cr) count':[ i[1] for i in list(d.values())]})
                temp = temp.sort_values(by=['amount (Cr) sum','amount (Cr) count'],ascending=[False, False]).head(1)
                temp.insert(0,'year',year)
                return temp
 
        for year in df['year'].unique():
            temp = year_wise_analysis(year)
            df_empty = pd.concat([df_empty, temp], ignore_index=False).reset_index(drop=True)
        st.dataframe(df_empty)



    st.subheader('Investments vs. Sector') 
    selected_option = st.selectbox('Select Type',['Sum','Count'])
    if selected_option == 'Sum':
        df_sec_amount = df.groupby('vertical')['amount (Cr)'].sum().reset_index()
        df_sec_amount = df_sec_amount[df_sec_amount['amount (Cr)']>0]

    else:
        df_sec_amount = df.groupby('vertical')['amount (Cr)'].count().reset_index()
        df_sec_amount = df_sec_amount[df_sec_amount['amount (Cr)']>0]
        
    color_scale = px.colors.sequential.Plasma
    normed_values = df_sec_amount['amount (Cr)'] / df_sec_amount['amount (Cr)'].max()
    colors = [color_scale[int(value * (len(color_scale) - 1))] for value in normed_values]       
    pie_chart = go.Figure(go.Pie(
        labels=df_sec_amount['vertical'],
        values=df_sec_amount['amount (Cr)'],
        marker=dict(colors=colors), 
        textinfo='none'
        
    ))
    st.plotly_chart(pie_chart)
    st.subheader('More analysis') 
    selected_option = st.selectbox('Select Type',['City','Round'])
    if selected_option == 'City':
        temp_df = df.groupby('city')['amount (Cr)'].sum().sort_values(ascending=False).reset_index()
        temp_df=temp_df[temp_df['amount (Cr)']>0]
        x = 'city'
    else:
        temp_df = df.groupby('round')['amount (Cr)'].sum().sort_values(ascending=False).reset_index()
        temp_df=temp_df[temp_df['amount (Cr)']>0]
        x = 'round'
    bar_chart = go.Figure(data=[go.Bar(x=temp_df[x], y=temp_df['amount (Cr)'],
                                       marker=dict(
                                                color=temp_df['amount (Cr)'], 
                                                colorscale='Plasma', 
                                                colorbar=dict(title='Scale') ))])
    bar_chart.update_layout(
    yaxis=dict(
        type='log', 
    )
)
    st.plotly_chart(bar_chart)
    

# Analysis from investor's POV
def load_investor_details(investor):
    st.title(investor.capitalize())
    st.markdown('---')
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Most Recent Investments')
        recents = df[df['investors'].str.contains(investor)].head(5)[['date','startup','vertical','city','round','amount (Cr)']]
        st.dataframe(recents)
        st.write("Note: the 0 in 'amount (Cr)' column mean amount is undisclosed.")

    with col2:
        freq_investments_count = df[df['investors'].str.contains(investor)].startup.value_counts()
        max_count = freq_investments_count.max()
        if max_count>1:
            st.subheader('Frequent Investments')
            freq_investments = freq_investments_count[freq_investments_count == max_count]
            st.dataframe(freq_investments)    
    st.markdown('---')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader('Biggest Investments')
        biggests = df[df['investors'].str.contains(investor)].groupby('startup')['amount (Cr)'].sum().sort_values(ascending=False).head()
        st.dataframe(biggests)

    with col2:
        st.subheader('Startups vs Investments')
        bar_chart = px.bar(biggests.reset_index(), x='startup', y='amount (Cr)', color='amount (Cr)', color_continuous_scale='Plasma')
        st.plotly_chart(bar_chart)

    with col3:
        temp = df[df['investors'].str.contains(investor)].groupby('vertical')['amount (Cr)'].sum().sort_values(ascending=False).head()
        temp = temp.reset_index()
        color_scale = px.colors.sequential.Plasma
        normed_values = temp['amount (Cr)'] / temp['amount (Cr)'].max()
        colors = [color_scale[int(value * (len(color_scale) - 1))] for value in normed_values]
        st.subheader('Investments per Sector')        
        pie_chart = go.Figure(go.Pie(
            labels=temp['vertical'],
            values=temp['amount (Cr)'],
            marker=dict(colors=colors),  # Apply the gradient colors
            
        ))
        pie_chart.update_layout(showlegend=False)
        # pie_chart = px.pie(temp.reset_index(), names='vertical', values='amount (Cr)', color='amount (Cr)', color_continuous_scale='Plasma', title='Investments in each Sector')
        st.plotly_chart(pie_chart)
    
    year_series = df[df['investors'].str.contains(investor)].groupby('year')['amount (Cr)'].sum()
    st.subheader('YoY Investment')
    if len(year_series)<=1:
        st.warning("Sorry, too much less data for a YoY analysis.")
    else:
        line_chart = px.line(year_series.reset_index(), x='year', y='amount (Cr)')
        st.plotly_chart(line_chart)


# Analysis from startup's POV
def load_startup_details(startup):
    st.title(startup)
    st.subheader(df[df['startup']==startup]['vertical'].values[0]+","+df[df['startup']==startup]['city'].values[0])
    st.markdown('---')
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Most Recent Investments')
        recents = df[df['startup']==startup].head(5)[['date','investors','round','amount (Cr)']]
        st.dataframe(recents)
        st.write("Note: the 0 in 'amount (Cr)' column mean amount is undisclosed.")

    with col2:
        d={}
        def find_investors(row):
            t1 = str(row['investors']).split(',')
            t = [i.strip() for i in t1]
            for i in t:
                if i not in d:
                    d[i] = [row['amount (Cr)'],1]
                else:
                    d[i][0] += row['amount (Cr)']
                    d[i][1] += 1
            return row['investors']
        df['investors'] = df[df['startup']==startup].apply(find_investors, axis = 1)
        investors_amount_df = pd.DataFrame({'Investors':list(d.keys()),
                                'Amount (Cr)':[ i[0] for i in list(d.values())]})
        investors_count_df = pd.DataFrame({'Investors':list(d.keys()),
                                'Count':[ i[1] for i in list(d.values())]})
        max_count = investors_count_df['Count'].max()
        if max_count>1:
            st.subheader('Frequent Investors')
            freq_investors = investors_count_df[investors_count_df['Count'] == max_count]
            st.dataframe(freq_investors) 
    st.markdown('---')

    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Investors vs Investments')
        if investors_amount_df.shape[0]==0 or (investors_amount_df.shape[0]==1 and investors_amount_df.iloc[0]['Amount (Cr)']==0):
            st.warning("Sorry. We couldn't find sufficient data!")
        else:

            bar_chart = px.bar(investors_amount_df, x='Investors', y='Amount (Cr)', color='Amount (Cr)', color_continuous_scale='Plasma')
            st.plotly_chart(bar_chart)

    with col2:
        year_series = df[df['startup']==startup].groupby('year')['amount (Cr)'].sum()
        st.subheader('YoY Investment')
        if len(year_series)<=1:
            st.warning("sorry, limited data. YoY graph not possible")
        else:
            line_chart = px.line(year_series.reset_index(), x='year', y='amount (Cr)')
            st.plotly_chart(line_chart)




if option == 'Overall Analysis':
    load_overall_analysis()
elif option == 'StartUp':
    selected_startup = st.sidebar.selectbox('Select StartUp',sorted(df['startup'].unique().tolist()))
    btn1 = st.sidebar.button('Find StartUp Details')
    if btn1:
        load_startup_details(selected_startup)
else:
    selected_investor = st.sidebar.selectbox('Select StartUp',investors_list)
    btn2 = st.sidebar.button('Find Investor Details')
    if btn2:
        load_investor_details(selected_investor)
