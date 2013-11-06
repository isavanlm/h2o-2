import unittest, random, sys, time
sys.path.extend(['.','..','py'])

import h2o, h2o_cmd, h2o_hosts, h2o_import as h2i, h2o_exec, h2o_glm, h2o_jobs

class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global localhost
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(node_count=1, java_heap_GB=10)
        else:
            h2o_hosts.build_cloud_with_hosts(node_count=1, java_heap_GB=10)

    @classmethod
    def tearDownClass(cls):
        h2o.tear_down_cloud()

    def test_GLM_prostate(self):
        h2o.beta_features=True
        importFolderPath = "logreg"
        csvFilename = 'prostate.csv'
        csvPathname = importFolderPath + "/" + csvFilename
        hex_key = csvFilename + ".hex"

        parseResult = h2i.import_parse(bucket='smalldata', path=csvPathname, schema='local', hex_key=hex_key, 
             timeoutSecs=180, noPoll=True, doSummary=False)
        h2o_jobs.pollWaitJobs(timeoutSecs=300, pollTimeoutSecs=300, retryDelaySecs=5)
        inspect = h2o_cmd.runInspect(None, parseResult['destination_key'])
        print inspect
        print "\n" + csvPathname, \
            "    numRows:", "{:,}".format(inspect['numRows']), \
            "    numCols:", "{:,}".format(inspect['numCols'])

        x         = 'ID'
        y         = 'CAPSULE'
        family    = 'binomial'
        alpha     = '0.5'
        lambda_   = '1E-4'
        nfolds    = '5' # fails
        nfolds    = '0'
        case_mode = '='
        case_val  = '1'
        f         = 'prostate'
        modelKey  = 'GLM(' + f + ')'

        kwargs = {       'response'          : y,
                         'ignored_cols'       : x,
                         'family'             : family,
                         'lambda'             : lambda_,
                         'alpha'              : alpha,
                         'n_folds'            : nfolds, # passes if 0, fails otherwise
                         #'case_mode'          : case_mode,
                         #'case_val'           : case_val, 
                         'destination_key'    : modelKey,
                 }


        timeoutSecs = 60
        start = time.time()
        glmFirstResult = h2o_cmd.runGLM(parseResult=parseResult, timeoutSecs=timeoutSecs, retryDelaySecs=0.25, pollTimeoutSecs=180, noPoll=True, **kwargs)

        h2o_jobs.pollWaitJobs(timeoutSecs=300, pollTimeoutSecs=300, retryDelaySecs=5)
        print "FIX! how do we get the GLM result"
        # hack it!
        job_key = glmFirstResult['job_key']

        # is the job finishing before polling would say it's done?
        params = {'job_key': job_key, 'destination_key': modelKey}
        a = h2o.nodes[0].completion_redirect(jsonRequest="2/GLMProgressPage2.json", params=params)
        print "GLM result from completion_redirect:", h2o.dump_json(a)

        a = h2o.nodes[0].glm_view(_modelKey=modelKey)
        print "GLM result from glm_view:", h2o.dump_json(a)

        # how do we get to the model view?
        # http://192.168.0.37:54321/2/GLMModelView.html?_modelKey=GLM2_59af6ba2-3321-4a6a-84ed-16b44a087707



if __name__ == '__main__':
    h2o.unit_main()
