import jenkins.model.Jenkins

Jenkins.get().pluginManager.plugins.each {
  println "${it.getShortName()}:${it.getVersion()}"
}
