import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.reasoner.*;
import org.semanticweb.owlapi.profiles.*;
import org.semanticweb.HermiT.Reasoner;

/** OWLAPI + HermiT bundled in Owlready2. No GUI, no network imports. */
public class ValidateOntology {
  public static void main(String[] args) throws Exception {
    OWLOntologyManager manager=OWLManager.createOWLOntologyManager();
    OWLOntology ontology=manager.loadOntologyFromOntologyDocument(new File(args[0]));
    OWLProfileReport profile=new OWL2DLProfile().checkOntology(ontology);
    System.out.println("owl2dl="+profile.isInProfile());
    if(!profile.isInProfile()) for(OWLProfileViolation v:profile.getViolations()) System.out.println("profile_violation="+v);
    OWLReasoner r=new Reasoner.ReasonerFactory().createReasoner(ontology);
    boolean ok=r.isConsistent();System.out.println("consistent="+ok);
    if(!ok){r.dispose();System.exit(2);}
    r.precomputeInferences(InferenceType.CLASS_HIERARCHY,InferenceType.CLASS_ASSERTIONS,InferenceType.OBJECT_PROPERTY_ASSERTIONS);
    Set<OWLClass> unsat=r.getUnsatisfiableClasses().getEntitiesMinusBottom();
    System.out.println("unsatisfiable_classes="+unsat.size());
    for(OWLClass c:unsat)System.out.println("unsatisfiable="+c.getIRI());
    int n=0;
    if(args.length>1){
      try(PrintWriter out=new PrintWriter(new OutputStreamWriter(new FileOutputStream(args[1]),StandardCharsets.UTF_8))){
        for(OWLNamedIndividual i:ontology.getIndividualsInSignature()){
          for(OWLClass c:r.getTypes(i,false).getFlattened()){
            if(!c.isOWLThing()){out.println("<"+i.getIRI()+"> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <"+c.getIRI()+"> .");n++;}
          }
          for(OWLObjectProperty p:ontology.getObjectPropertiesInSignature()){
            for(OWLNamedIndividual j:r.getObjectPropertyValues(i,p).getFlattened()){
              out.println("<"+i.getIRI()+"> <"+p.getIRI()+"> <"+j.getIRI()+"> .");n++;
            }
          }
        }
      }
    }
    System.out.println("entailed_named_assertions="+n);
    r.dispose();
    if(!unsat.isEmpty())System.exit(3);
  }
}
