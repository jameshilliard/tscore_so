# Copyright 2013-2014 by Contec. All Rights Reserved.
#

"""
This is the main program that will create 
system wide processes and resources and
manage messages between the processes.
"""
import sys
import time
import logging
import json

from multiprocessing import Process
from multiprocessing import Queue

from frwk_test_process import test_main
from frwk_debug_process import debug_main
from frwk_ui_process import ui_main

class MainState():
    """
        Class to hold the states of the main process
    """
    slot_barcode = ''
    emp_id = ''  # operator employee id
    dut_barcode  = ''
    test_num = ''
    state = 'INIT'
    msgFromUi = ''
    test_proc_state = 'INIT'
    msgFromTest = {}
    debug_proc_state = 'INIT'
    msgFromDebug = []

    def __init__(self):
        """
        Constructor
        """
        pass
    
def _create_test_process(_logger, test_to_mainQ, main_to_testQ):
    """
        Creates test process and provides the queues necessary 
        for test process to communicate with Main process.
        Args:
            _logger:          Logger handle for use within main process
            test_to_mainQ:    Queue for transmit from test process to main process
            main_to_testQ:    Queue for transmit from main process to test process
        Returns:
            none
    """
    try:
        _debug_process = Process(target = test_main, args = (test_to_mainQ, main_to_testQ))
        _debug_process.start()
        _logger.info('Creation of Test processes completed.') 
    except:
        _logger.error('Unable to create Test process')
        sys.exit()

def _create_debug_process(_logger, debug_to_mainQ, main_to_debugQ):
    """
        Creates debug process and provides the queues necessary 
        for debug process to communicate with Main process.
        Args:
            _logger:          Logger handle for use within main process
            debug_to_mainQ:    Queue for transmit from debug to main process
            main_to_debugQ:    Queue for transmit from main to debug process
        Returns:
            none
    """
    try:
        _debug_process = Process(target = debug_main, args = (debug_to_mainQ, main_to_debugQ))
        _debug_process.start()
        _logger.info('Creation of Debug processes completed.') 
    except:
        _logger.error('Unable to create Debug process')
        sys.exit()


def _create_ui_process(_logger, ui_to_mainQ, main_to_uiQ):
    """
        Creates UI process and provides the queues necessary 
        for UI process to communicate with Main process.
        Args:
            _logger:        Logger handle for use within main process
            ui_to_mainQ:    Queue for transmit from UI process to main process
            main_to_uiQ:    Queue for transmit from main process to UI process
        Returns:
            none
    """
    try:
        _ui_process = Process(target = ui_main, args = (ui_to_mainQ, main_to_uiQ))
        _ui_process.start()
        _logger.info('Creation of UI processes completed.')
    except:
        _logger.error('Unable to create UI process')
        sys.exit()


def _process_slotid_msg(state_obj, main_to_uiQ):
    """
        Process received slotid from the UI process, Slotid
        can be received at any time and triggers a new DUT
        is being tested and the states are reset. Slotid is
        checked with respect to configuration file against
        all the available slots.
        @type state_obj StateObj
        @type main_to_uiQ Queue

    """
    # Check if slot ID in the dictionary
    jmsg = {}
    jmsg['CMD'] = state_obj.msgFromUi['CMD']
    jmsg['SLOTID'] = state_obj.msgFromUi['SLOTID']
    state_obj.slot_barcode = state_obj.msgFromUi['SLOTID']
    state_obj.emp_id = state_obj.msgFromUi['EMPID']
    state_obj.state = 'RECEIVED_SLOTID'
    send_msg = [json.dumps(jmsg)]
    _send_msg_to_ui(send_msg, main_to_uiQ)  # ACK message to UI process
    
    
def _process_dutbarcode_msg(state_obj, main_to_uiQ):
    """
        Process received barcode from the UI process, check if
        the main process has already received the slotid and 
        capable of receiving the DUT barcode.
        Args:
            state_obj:    State object that has main process state information
            main_to_uiQ:  Queue for sending messages from this process to UI process
        Returns:
            none
    """
    jmsg = {}
    jmsg['CMD'] = state_obj.msgFromUi['CMD']   
    jmsg['DUTBARCODE'] = state_obj.msgFromUi.get('DUTBARCODE','')
    # Process must have received SLOT ID
    if (state_obj.state != 'RECEIVED_SLOTID'):
        jmsg['ERROR'] = 'ERROR_INVALIDSLOTID'
        send_msg = [json.dumps(jmsg)]
        _send_msg_to_ui(send_msg, main_to_uiQ) # ACK message to UI process
        return(False)
    
    if (len(state_obj.msgFromUi.get('DUTBARCODE','')) > 0):
        state_obj.dut_barcode = state_obj.msgFromUi.get('DUTBARCODE','').upper()
        state_obj.state = 'RECEIVED_DUTBARCODE'
        jmsg['ERROR'] = 'NOERROR'
    else:
        jmsg['ERROR'] = 'ERROR_INVALIDBARCODE'
    send_msg = [json.dumps(jmsg)]
    _send_msg_to_ui(send_msg, main_to_uiQ) # ACK message to UI process
    
    
def _process_testid_msg(state_obj, main_to_uiQ, main_to_testQ):
    """
    Execute the requested test, check if the main process
    current state is in DEBUG mode before starting to test.
    This function will not be used for RELEASE mode testing.
    Args:
        state_obj:        Main process state information object
        main_to_uiQ:      Main process to UI process transmit queue
        main_to_testQ:    Main process to test process transmit queue
    Returns:
        none
    """
    # TBD: Check if test ID available in DB
    # TBD: Get the required filters and graphs based on make & model
    # TBD: Execute the test
    # TBD: Send result to UI process about the test result

    # Check the current process state, we need to
    # be in the DEBUG mode for running test cases
    # discretely from the terminal.
    jmsg = {}
    jmsg['CMD'] = state_obj.msgFromUi['CMD']   
    if (state_obj.state != 'DEBUG'):
        jmsg['ERROR'] = 'ERROR_INVALIDPROCESSSTATE'
        send_msg = [json.dumps(jmsg)]
        _send_msg_to_ui(send_msg, main_to_uiQ)
        return(False)
    # Send message to test process for executing the test case
    jmsg = {}
    jmsg['CMD'] = state_obj.msgFromUi['CMD']   
    jmsg['DUTBARCODE'] = state_obj.dut_barcode
    jmsg['TESTID'] = state_obj.msgFromUi.get('TESTID','').upper()
    sendMsg = [json.dumps(jmsg)]
    _send_msg_to_test(sendMsg, main_to_testQ)
    return(True)
    
    
def _process_mode_msg(state_obj, main_to_uiQ):
    """
        Process received mode message. If the mode set by the user
        is DEBUG then all the tests are executed in discrete mode
        and if set to RELEASE mode, they are run in sequence mode.
        Args:
            state_obj:      Main process state object
            main_to_uiQ:    Main process to UI process message transmit Queue
        Returns:
            none
    """
    jmsg = {}
    jmsg['CMD'] = state_obj.msgFromUi['CMD']   
    jmsg['MODE'] = state_obj.msgFromUi.get('MODE','')
    # Check if the mode is right
    if ((state_obj.msgFromUi.get('MODE','').upper() != 'DEBUG') and (state_obj.msgFromUi.get('MODE','').upper() != 'RELEASE')):
        jmsg['ERROR'] = 'ERROR_INVALIDPROCESSSTATE'
        send_msg = [json.dumps(jmsg)]
        _send_msg_to_ui(send_msg, main_to_uiQ)
        return(False)

    # Check the current process state
    if ( (state_obj.state == 'RECEIVED_DUTBARCODE') or (state_obj.state == 'DEBUG') or (state_obj.state == 'RELEASE')):
        state_obj.state = state_obj.msgFromUi.get('MODE','').upper()
        jmsg['ERROR'] = 'NOERROR'
        send_msg = [json.dumps(jmsg)]
        _send_msg_to_ui(send_msg, main_to_uiQ)
        return(True)
    else: 
        jmsg['ERROR'] = 'ERROR_INVALIDPROCESSSTATE'
        send_msg = [json.dumps(jmsg)]
        _send_msg_to_ui(send_msg, main_to_uiQ)
        return(False)

def _process_stoptest_msg(state_obj,main_to_testQ):
    print "[MAINPROC] MAIN PROC ---> SENDING question request"
    send_msg_to_test = [json.dumps(state_obj.msgFromUi)]
    _send_msg_to_test(send_msg_to_test, main_to_testQ)

def _process_getstate_msg(state_obj,main_to_uiQ):
     msg = {}
     msg['CMD'] = state_obj.msgFromUi['CMD']
     msg['mainstate'] = state_obj.state
     msg['testprstate'] = state_obj.test_proc_state
     msg['DUTBARCODE'] = state_obj.dut_barcode
     send_msg = [json.dumps(msg)]
     #print 'sending msg:',send_msg
     _send_msg_to_ui(send_msg, main_to_uiQ)
     return(True)
def _process_useranswer_msg(state_obj,main_to_testQ):
     print "[MAINPROC] MAIN PROC ---> SENDING USER ANSWER:"
     send_msg_to_test = [json.dumps(state_obj.msgFromUi)]
     _send_msg_to_test(send_msg_to_test, main_to_testQ)

def _process_getuserinputq_msg(state_obj,main_to_testQ):
     print "[MAINPROC] MAIN PROC ---> SENDING question request"
     send_msg_to_test = [json.dumps(state_obj.msgFromUi)]
     _send_msg_to_test(send_msg_to_test, main_to_testQ)


def _process_help_msg(state_obj,main_to_uiQ):
    """
        Process received help message from the UI process
        Args:
            main_to_uiQ:    Main process to UI process message transmit Queue
        Returns:
            none
    """
    help_msg =  '\n\n** Commands **\n' + \
                '--------------\n' + \
                'SLOTID      , slot_number_like_10021\n' +  \
                'DUTBARCODE  , dut_barcode_like_CSJE9211213039\n' + \
                'MODE        , DEBUG or RELEASE \n' + \
                'TESTID      , test_to_execute_like_VZ00020 \n' + \
                'HELP\n\n'
    msg = {}
    msg['CMD'] = state_obj.msgFromUi['CMD']
    msg['HELP_MSG'] = help_msg
    send_msg = [json.dumps(msg)]            
    _send_msg_to_ui(send_msg, main_to_uiQ)  # ACK message to UI process


def _process_invalid_msg(state_obj, main_to_uiQ):
    """
        Process received invalid/not supported message from the UI process
        Args:
            state_obj:      Main process state object
            main_to_uiQ:    Main process to UI process message transmit Queue
        Returns:
            none
    """
    jmsg = {}
    jmsg['CMD'] = state_obj.msgFromUi['CMD']   
    jmsg['ERROR'] = 'ERROR_INVALIDPROCESSSTATE'
    send_msg = [json.dumps(jmsg)]
    #send_msg = [state_obj.msgFromUi[0], 'ERROR_INVALIDCOMMAND']            
    _send_msg_to_ui(send_msg, main_to_uiQ)  # ACK message to UI process
 
    
def _process_release_mode_test(state_obj, main_to_testQ):
    """
        Process the RELEASE mode of the test. Trigger the 
        release mode testing to be carried out for the given
        DUT barcode in the test process.
        Args:
            state_obj:        Main process state object
            main_to_uiQ:      Transmit queue from main to ui process
        Returns:
            none
    """
    # Build Release mode test message
    jmsg = {}
    jmsg['CMD'] = 'RELEASE'   
    jmsg['DUTBARCODE'] = state_obj.dut_barcode
    jmsg['SLOTID'] = state_obj.slot_barcode
    jmsg['EMPID'] = state_obj.emp_id
    sendMsg = [json.dumps(jmsg)]
    _send_msg_to_test(sendMsg, main_to_testQ) 
    return (True)

def _process_debug_mode_test(state_obj, main_to_testQ):
    """
        Process the DEBUG mode of the test. 
        Args:
            state_obj:        Main process state object
            main_to_uiQ:      Transmit queue from main to ui process
        Returns:
            none
    """
    # state_obj.msgFromUi[0] - Mode
    # state_obj.msgFromUi[1] - Test case number
    jmsg = {}
    jmsg['CMD'] = 'DEBUG'   
    jmsg['DUTBARCODE'] = state_obj.dut_barcode
    sendMsg = [json.dumps(jmsg)]
    _send_msg_to_test(sendMsg, main_to_testQ) 
    return (True)

def _send_msg_to_ui(msgList, main_to_uiQ):
    """
        Function that send message list from main process
        to the UI process.
        Args:
            msgList:        Transmit message list 
            main_to_uiQ:    Transmit queue from main process to UI process
        Returns:
            none
    """
    try:
        main_to_uiQ.put(msgList)
    except:
        print "[MAINPROC] MAIN PROC ---> UI PROC: send exception"

def _send_msg_to_debug(msgList, main_to_debugQ):
    """
        Function that send message list from main process
        to the Debug process.
        Args:
            msgList:            Transmit message list 
            main_to_debugQ:     Transmit queue from main process to debug process
        Returns:
            none
    """
    try:
        main_to_debugQ.put(msgList)
    except:
        print "[MAINPROC] MAIN PROC ---> DEBUG PROC: send exception"
      
def _send_msg_to_test(msgList, main_to_testQ):
    """
        Function that send message list from main process
        to the Test process.
        Args:
            msgList:           Transmit message list 
            main_to_testQ:     Transmit queue from main to test process
        Returns:
            none
    """
    try:
        main_to_testQ.put(msgList)
    except:
        print "[MAINPROC] MAIN PROC ---> TEST PROC: send exception"
    

def _process_msg_from_ui(ui_to_mainQ, main_to_uiQ, main_to_testQ, state_obj):
    """
        Function that processes the messages from the UI process
        and take appropriate action based on the received messages.
        Args:
            ui_to_mainQ:    Queue where messages from UI process are received
            main_to_uiQ:    Transmit queue from main process to UI process
            main_to_testQ:  Transmit queue from main process to Test process
            state_obj:      Main process state object
        Returns:
            none
    """
    try:
        msgFromUi = ui_to_mainQ.get(block=False);
        print "[MAINPROC] MAIN PROC <--- UI PROC :", msgFromUi
    except:
        msgFromUi = '' # No message
        return (False)
    
    # Check the command and take action
    if (len(msgFromUi) < 1):
        return(False)
    
    # Make a copy of the message for future use
    #state_obj.msgFromUi = list(msgFromUi)
    jsMsgFromUi = None
    try:
        jsMsgFromUi = json.loads(msgFromUi)
    except:
        print "[MAINPROC] MAIN PROC <--- UI PROC :error while parsing json"
    state_obj.msgFromUi = jsMsgFromUi
    # Process command
    if (jsMsgFromUi['CMD'] == 'SETSLOTID'):
        _process_slotid_msg(state_obj, main_to_uiQ)
    elif (jsMsgFromUi['CMD'] == 'SETDUTBARCODE'):
        _process_dutbarcode_msg(state_obj, main_to_uiQ)
    elif (jsMsgFromUi['CMD'] == 'SETMODE'):
        retVal = _process_mode_msg(state_obj, main_to_uiQ)
        if (retVal == True):
            # Check if the mode is RELEASE 
            if (state_obj.state == 'RELEASE'):
                _process_release_mode_test(state_obj, main_to_testQ)
            elif (state_obj.state == 'DEBUG'):
                _process_debug_mode_test(state_obj, main_to_testQ)
            else:
                pass
        else:
            pass
    elif (jsMsgFromUi['CMD'] == 'STOPTEST'):
        _process_stoptest_msg(state_obj, main_to_testQ)
    elif (jsMsgFromUi['CMD'] == 'SETTESTID'):
        _process_testid_msg(state_obj, main_to_uiQ, main_to_testQ)
    elif (jsMsgFromUi['CMD'] == 'HELP'):
        _process_help_msg(state_obj,main_to_uiQ)
    elif (jsMsgFromUi['CMD'] == 'GETSTATE'):
        _process_getstate_msg(state_obj,main_to_uiQ)
    elif (jsMsgFromUi['CMD'] == 'TEST_GETUSERINPUTQ'):
        _process_getuserinputq_msg(state_obj,main_to_testQ)
    elif (jsMsgFromUi['CMD'] == 'TEST_USERINPUTANSWER'):
        _process_useranswer_msg(state_obj,main_to_testQ)
    else:
        _process_invalid_msg(state_obj, main_to_uiQ)

    
def _process_msg_from_debug(debug_to_mainQ, main_to_debugQ):
    """
        Process messages from the display process
        Args:
            debug_to_mainQ:    Queue for receiving messages from display to main process
            main_to_debugQ:    Queue for transmitting messages from main to debug process
        Returns:
            none
    """
    try:
        msgFromDebug = debug_to_mainQ.get(block=False);
        print "[MAINPROC] MAIN PROC <--- DEBG PROC :", msgFromDebug
        '''
        ### test echo---------------------------------------------------#
        try:                                                            #
            main_to_debugQ.put(msgFromDebug)                            #
        except:                                                         #
            print "[MAINPROC] MAIN PROC ---> DEBG PROC: exception"      #
        ### test echo ends here ----------------------------------------#
        '''
    except:
        msgFromDebug = ''


def _process_msg_from_test (test_to_mainQ, main_to_testQ, main_to_uiQ, main_to_debugQ, state_obj):
    """
        Process messages from test process
        Args:
            test_to_mainQ:    Receive message queue from Test process
            main_to_testQ:    Transmit message queue from main to test process
        Returns:
            none
    """
    try:
        msgFromTest = test_to_mainQ.get(block=False);
        print "[MAINPROC] MAIN PROC <--- TEST PROC :", msgFromTest
    except:
        msgFromTest = '' # No message
        return (False)
    
    # Check for a command availability
    if (len(msgFromTest) < 1):
        return(False)

    jmsg = msgFromTest[0];
    jsMsgFromTest = None
    try:
        jsMsgFromTest = json.loads(jmsg)
    except:
        print "[MAINPROC] TET PROC <--- MAIN PROC :error while parsing json"
        return
    # Make a copy of the message for future use
    state_obj.msgFromTest = jsMsgFromTest
    cmd = jsMsgFromTest.get('CMD','').upper()
    error = jsMsgFromTest.get('ERROR','').upper()
    if error != 'NOERROR' and len(error) > 0:
         _process_test_error_msg(state_obj, main_to_testQ)
         _send_msg_to_ui(msgFromTest, main_to_uiQ)
         return;
        
   

    # Process command
    if (cmd == 'TEST_STARTED'):
        _process_test_started_msg(state_obj, main_to_testQ)
    elif (cmd == 'TEST_ABORTED'):
        _process_test_aborted_msg(state_obj, main_to_testQ)
    elif (cmd == 'TEST_COMPLETED'):
        _process_test_completed_msg(state_obj, main_to_testQ)
    elif (cmd == 'TEST_ALLCOMPLETED'):
        _process_test_allcompleted_msg(state_obj, main_to_testQ)
    elif (cmd == 'TEST_PROGRESS'):
        _process_test_progress_msg(state_obj, main_to_testQ)
    elif (cmd == 'TEST_DEBUGMODESTARTED'):
        _process_test_debugmodestarted_msg(state_obj, main_to_testQ)
    elif (cmd == 'TEST_RELEASEMODESTARTED'):
        _process_test_releasemodestarted_msg(state_obj, main_to_testQ)
    elif (cmd == 'TEST_RESULT'):
        _process_test_result_msg(state_obj, main_to_testQ)
    elif (cmd == 'TEST_NOTIMPLEMENTED'):
        _process_test_notimplemented_msg(state_obj, main_to_testQ)
    else:
        _process_test_invalid_msg(state_obj, main_to_testQ)
    # Relay the message received to UI process & DEBUG process
    _send_msg_to_ui(msgFromTest, main_to_uiQ)
    #_send_msg_to_debug(msgFromTest, main_to_debugQ)

def _process_test_error_msg(state_obj, main_to_testQ):
      state_obj.state = 'INIT'
      state_obj.test_proc_state = 'INIT'
      state_obj.dut_barcode = ''

def _process_test_started_msg(state_obj, main_to_testQ):
    """
        Process test started message from test process, send 
        the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    state_obj.test_proc_state = 'TEST_STARTED'
    jmsg = {}
    jmsg['CMD'] = 'MAIN_ACK'   
    jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    _send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process

    
def _process_test_aborted_msg(state_obj, main_to_testQ):
    """
        Process test aborted message from test process, send 
        the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    state_obj.state = 'INIT'
    state_obj.test_proc_state = 'INIT'
    state_obj.dut_barcode = ''
    #jmsg = {}
    #jmsg['CMD'] = 'MAIN_ACK'
    #jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    #send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    #_send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process

    
def _process_test_completed_msg(state_obj, main_to_testQ):
    """
        Process test completed message from test process, send 
        the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    state_obj.test_proc_state = 'TEST_COMPLETED'
    jmsg = {}
    jmsg['CMD'] = 'MAIN_ACK'   
    jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    _send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process

def _process_test_progress_msg(state_obj, main_to_testQ):
    """
        Process progress message from test process,  
        send the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    state_obj.test_proc_state = 'TEST_PROGRESS'
    jmsg = {}
    jmsg['CMD'] = 'MAIN_ACK'   
    jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    _send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process


def _process_test_allcompleted_msg(state_obj, main_to_testQ):
    """
        Process all tests completed message from test process,  
        send the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    state_obj.test_proc_state = 'TEST_ALLCOMPLETED'
    jmsg = {}
    jmsg['CMD'] = 'MAIN_ACK'   
    jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    _send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process

    
def _process_test_debugmodestarted_msg(state_obj, main_to_testQ):
    """
        Process debug-mode message from test process,  
        send the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    state_obj.test_proc_state = 'TEST_DEBUGMODESTARTED'
    jmsg = {}
    jmsg['CMD'] = 'MAIN_ACK'   
    jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    _send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process


def _process_test_releasemodestarted_msg(state_obj, main_to_testQ):
    """
        Process release-mode message from test process,  
        send the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    state_obj.test_proc_state = 'TEST_RELEASEMODESTARTED'
    jmsg = {}
    jmsg['CMD'] = 'MAIN_ACK'   
    jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    _send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process

            
def _process_test_result_msg(state_obj, main_to_testQ):
    """
        Process test result message from test process,  
        send the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    jmsg = {}
    jmsg['CMD'] = 'MAIN_ACK'   
    jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    _send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process
    state_obj.state = 'INIT'
    state_obj.test_proc_state = 'INIT'
    state_obj.dut_barcode = ''

def _process_test_notimplemented_msg(state_obj, main_to_testQ):
    """
        Process test not implemented message from test process,  
        send the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    state_obj.test_proc_state = 'TEST_NOTIMPLEMENTED'
    jmsg = {}
    jmsg['CMD'] = 'MAIN_ACK'   
    jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    _send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process

def _process_test_invalid_msg(state_obj, main_to_testQ):
    """
        Process test invalid message from test process,  
        send the status to UI process and debug process.
        
        Args:
            state_obj:          Main process state object
            main_to_testQ:      Transmit queue from main(this) to test process
        Return:
            none
    """
    jmsg = {}
    jmsg['CMD'] = 'MAIN_ACK'   
    jmsg['ACK_CMD'] = state_obj.msgFromTest.get('CMD','')
    send_msg = [json.dumps(jmsg)]
    #send_msg = ['MAIN_ACK', state_obj.msgFromTest[0]]            
    _send_msg_to_test(send_msg, main_to_testQ)  # ACK message to TEST process
        
    
def main():
    """
        TScore main function
    """
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

    # Creation section
    ui_to_mainQ = Queue()   # UI process   -> Main process
    main_to_uiQ = Queue()   # Main process -> UI process
    
    main_to_debugQ = Queue() # Main process  -> Debug process
    debug_to_mainQ = Queue() # Debug process -> Main process 

    main_to_testQ = Queue() # Main process -> Test process
    test_to_mainQ = Queue() # Test process -> Main process 

    _logger.info('Creation of all queues completed.')

    _create_ui_process(_logger, ui_to_mainQ, main_to_uiQ)
    #_create_debug_process(_logger, debug_to_mainQ, main_to_debugQ)
    _create_test_process(_logger, test_to_mainQ, main_to_testQ)
    
    # Initialization section
    state_obj = MainState()
    
    # Processing section
    while (True):
        time.sleep(.5)
        _process_msg_from_ui(ui_to_mainQ, main_to_uiQ, main_to_testQ, state_obj)
        #_process_msg_from_debug(debug_to_mainQ, main_to_debugQ)
        _process_msg_from_test (test_to_mainQ, main_to_testQ, main_to_uiQ, main_to_debugQ, state_obj)
    #--- While ends here ---

##
## Main process
##
if __name__ == '__main__':
    main()
