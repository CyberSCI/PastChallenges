import groovy.json.JsonOutput

def credFiles = [
    '/shared/garage-creds.env',
    '/shared/jenkins-config-creds.env'
]

def data = [:]
credFiles.each { path ->
    def f = new File(path)
    data[path] = f.exists() ? f.text : null
}

println JsonOutput.toJson(data)
