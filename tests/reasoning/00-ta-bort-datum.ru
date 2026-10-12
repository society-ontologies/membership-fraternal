# Before reasoning: drop literals whose datatypes are not in the OWL 2 datatype
# map (xsd:date, xsd:gYear, xsd:gYearMonth). HermiT rejects them, and no
# inference in the stack depends on dates. SHACL still checks them.
#
# The update also round-trips the merged graph through RDF, which turns properties
# that a sample file uses but does not declare from annotations back into the object
# and datatype properties the stack declares. Keep it in every reasoning run, or domains,
# ranges and owl:hasValue do nothing; tests/reasoning/canary/ checks that they still apply.
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
DELETE { ?s ?p ?o }
WHERE {
    ?s ?p ?o .
    FILTER (isLiteral(?o) && datatype(?o) IN (xsd:date, xsd:gYear, xsd:gYearMonth))
}
