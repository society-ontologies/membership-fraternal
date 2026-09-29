# Before reasoning: drop literals whose datatypes are not in the OWL 2 datatype
# map (xsd:date, xsd:gYear, xsd:gYearMonth). HermiT rejects them, and no
# inference in the stack depends on dates. SHACL still checks them.
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
DELETE { ?s ?p ?o }
WHERE {
    ?s ?p ?o .
    FILTER (isLiteral(?o) && datatype(?o) IN (xsd:date, xsd:gYear, xsd:gYearMonth))
}
