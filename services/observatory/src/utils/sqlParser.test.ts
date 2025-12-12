/**
 * Test file for extractSourceTables function
 * Run with: npx tsx src/utils/sqlParser.test.ts
 */

import { extractSourceTables } from './sqlParser'

// Test case 1: Compiled dbt SQL with quoted identifiers
const compiledDbtSql = `
-- fct_daily_github_metrics.sql - Gold layer daily GitHub activity metrics fact table
-- Creates an incrementally updated fact table with daily GitHub activity metrics

/*
Daily GitHub activity metrics fact table
*/

select
    event_date as activity_date,
    day_name,
    day_of_week,
    extract(month from event_date) as month,
    extract(year from event_date) as year,
    count(*) as total_events

from "iceberg"."bronze"."fct_github_events"

where event_date > (select coalesce(max(activity_date), date('1900-01-01')) from "iceberg"."bronze"."fct_daily_github_metrics")

group by event_date, day_name, day_of_week
order by activity_date desc
`

// Test case 2: Simple unquoted table name
const simpleSql = `
SELECT * FROM my_table WHERE id = 1
`

// Test case 3: SQL with EXTRACT function (should not match)
const extractSql = `
SELECT extract(month from date_column) as month FROM users
`

// Test case 4: SQL with JOIN
const joinSql = `
SELECT a.*, b.name
FROM "iceberg"."gold"."orders" a
JOIN "iceberg"."gold"."customers" b ON a.customer_id = b.id
`

// Test case 5: Raw dbt SQL with {{ ref() }} syntax
const rawDbtSql = `
-- dbt model: fct_daily_github_metrics.sql

{{ config(
    materialized='incremental',
    unique_key='activity_date'
) }}

select
    event_date as activity_date,
    count(*) as total_events
from {{ ref('fct_github_events') }}
group by event_date
`

// Test case 6: Raw dbt SQL without ref() - just table name
const rawDbtNoRef = `
-- My dbt model
select * from my_source_table where id > 0
`

// Run tests
console.log('=== Test 1: Compiled dbt SQL with quoted identifiers ===')
const result1 = extractSourceTables(compiledDbtSql)
console.log('Expected: ["fct_github_events"]')
console.log('Got:', result1)
console.log('Pass:', result1.includes('fct_github_events'))
console.log()

console.log('=== Test 2: Simple unquoted table name ===')
const result2 = extractSourceTables(simpleSql)
console.log('Expected: ["my_table"]')
console.log('Got:', result2)
console.log('Pass:', result2.includes('my_table'))
console.log()

console.log('=== Test 3: SQL with EXTRACT function ===')
const result3 = extractSourceTables(extractSql)
console.log('Expected: ["users"]')
console.log('Got:', result3)
console.log(
  'Pass:',
  result3.includes('users') && !result3.includes('date_column'),
)
console.log()

console.log('=== Test 4: SQL with JOIN ===')
const result4 = extractSourceTables(joinSql)
console.log('Expected: ["orders", "customers"]')
console.log('Got:', result4)
console.log(
  'Pass:',
  result4.includes('orders') && result4.includes('customers'),
)
console.log()

console.log('=== Test 5: Raw dbt SQL with {{ ref() }} syntax ===')
const result5 = extractSourceTables(rawDbtSql)
console.log('Expected: ["fct_github_events"]')
console.log('Got:', result5)
console.log('Pass:', result5.includes('fct_github_events'))
console.log()

console.log('=== Test 6: Raw dbt SQL without ref() ===')
const result6 = extractSourceTables(rawDbtNoRef)
console.log('Expected: ["my_source_table"]')
console.log('Got:', result6)
console.log('Pass:', result6.includes('my_source_table'))
console.log()

// Import additional functions for testing
import {
  analyzeSQLTransformation,
  buildSmartWhereClause,
  parseColumnMappings,
} from './sqlParser'

// Test 7: Column mapping extraction from compiled dbt SQL
console.log('=== Test 7: Column mapping extraction ===')
const mappings = parseColumnMappings(compiledDbtSql)
console.log('Column mappings found:', mappings.length)
mappings.forEach((m) => {
  console.log(`  ${m.targetColumn} <- ${m.sourceColumn || m.sourceExpression}`)
})
// Check if activity_date -> event_date mapping exists
const activityDateMapping = mappings.find(
  (m) => m.targetColumn === 'activity_date',
)
console.log('activity_date mapping:', activityDateMapping)
console.log('Pass:', activityDateMapping?.sourceColumn === 'event_date')
console.log()

// Test 8: Full SQL analysis
console.log('=== Test 8: Full SQL analysis ===')
const analysis = analyzeSQLTransformation(compiledDbtSql)
console.log('Source tables:', analysis.sourceTables)
console.log('Transform type:', analysis.transformType)
console.log('Column mappings count:', analysis.columnMappings.length)
console.log()

// Test 9: Build WHERE clause with mapping
console.log('=== Test 9: Build smart WHERE clause ===')
const sampleRowData = {
  activity_date: '2025-12-02',
  total_events: 42,
}
const { whereClause, usedColumns, strategy } = buildSmartWhereClause(
  sampleRowData,
  analysis.columnMappings,
)
console.log('Row data:', sampleRowData)
console.log('WHERE clause:', whereClause)
console.log('Used columns:', usedColumns)
console.log('Strategy:', strategy)
// The WHERE clause should use source column names, not downstream names
console.log(
  'Pass:',
  whereClause.includes('event_date') || whereClause.includes('activity_date'),
)
console.log()
